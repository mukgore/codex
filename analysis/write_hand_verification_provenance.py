"""Write hashes and run metadata for the completed external hand benchmark."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


SOURCE_FILES = (
    "analysis/external_hand_verification.py",
    "analysis/hand_pose_metrics.py",
    "analysis/train_realtime_occluded_hand_models.py",
    "analysis/measure_hamer_pose.py",
    "analysis/occluded_pose_benchmark.py",
    "analysis/export_occlusion_previews.py",
    "analysis/render_external_hand_report.py",
    "analysis/write_hand_verification_provenance.py",
    "docs/reproducibility/hand_pose_metric_audit.md",
    "docs/reproducibility/realtime_occluded_hand_models.md",
    "tests/test_hand_pose_metrics.py",
    "tests/test_realtime_occluded_hand_models.py",
)
RUN_FILES = (
    "local_predictions.json", "realtime_predictions.json", "hamer_predictions.json",
    "mediapipe_predictions.json", "external_hand_verification.json",
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def make_provenance(repo: Path, results: Path, models: Path,
                    synthetic: Path, recorded: Path, output: Path):
    repo, results, models = repo.resolve(), results.resolve(), models.resolve()
    synthetic, recorded, output = synthetic.resolve(), recorded.resolve(), output.resolve()
    code = {name: digest(repo / name) for name in SOURCE_FILES}
    data_index = json.loads((results / "occlusion_previews" / "index.json").read_text(encoding="utf-8"))
    datasets = {
        "external": {
            "name": "GigaHands official demo sequences; CC BY-NC 4.0",
            "root": str((results.parent / "extracted" / "hand_pose").resolve()),
            "preview_index_sha256": digest(results / "occlusion_previews" / "index.json"),
            "videos": [{"file": r["video"], "session": r["session"], "frames": r["frames"],
                        "source_sha256": r["video_sha256"], "labels_sha256": r["label_sha256"]}
                       for r in data_index],
        },
        "synthetic": {"root": str(synthetic),
                      "annotations_sha256": digest(synthetic / "annotations.json")},
        "recorded_training": {"root": str(recorded),
                              "pool_manifest_sha256": digest(recorded / "pool_manifest.json")},
    }
    runs = {}
    environments = {}
    for name in RUN_FILES:
        path = results / name
        runs[name] = {"sha256": digest(path), "size_bytes": path.stat().st_size}
    for backend in ("local", "realtime", "hamer", "mediapipe"):
        pred = json.loads((results / f"{backend}_predictions.json").read_text(encoding="utf-8"))
        environments[backend] = pred.get("environment", {})
    checkpoints = {p.name: {"sha256": digest(p), "size_bytes": p.stat().st_size}
                   for p in sorted(models.glob("*.pt"))}
    training_report = models / "report.json"
    resource_probes = {p.name: {"sha256": digest(p), "size_bytes": p.stat().st_size}
                       for p in sorted((results / "resource-probe").glob("*.json"))}
    previews = {p.name: {"sha256": digest(p), "size_bytes": p.stat().st_size}
                for p in sorted((results / "occlusion_previews").glob("*.mp4"))}
    document = {
        "schema": "hand-pose-independent-verification-provenance-v1",
        "repository": {"path": str(repo), "branch": git(repo, "branch", "--show-current"),
                       "head_commit": git(repo, "rev-parse", "HEAD"),
                       "working_tree_status": git(repo, "status", "--short"),
                       "source_sha256": code},
        "mask": {"canvas_px": [512, 420], "center_px": [256, 210], "radius_px": 95,
                 "rgb": [7, 11, 16], "applied_every_frame": True,
                 "joint_hidden_rule": "annotated point-center distance <= 95 px; boundary included"},
        "datasets": datasets,
        "commands": {
            "train_ab": "python analysis/train_realtime_occluded_hand_models.py --synthetic <occluded-pose-pilot-v14> --recorded <handcaptcha-live-motion> --output-dir <realtime-hand-models-v1> --epochs 16",
            "local_backend": "python analysis/external_hand_verification.py --backend local --data-root <extracted/hand_pose> --weights-dir analysis/occluded_pose_benchmark/results/grouped-v15/ridge-weights --output-dir <results>",
            "realtime_backend": "python analysis/external_hand_verification.py --backend realtime --data-root <extracted/hand_pose> --weights-dir analysis/occluded_pose_benchmark/results/grouped-v15/ridge-weights --realtime-models <realtime-hand-models-v1> --output-dir <results>",
            "hamer_backend": "python analysis/external_hand_verification.py --backend hamer --data-root <extracted/hand_pose> --weights-dir analysis/occluded_pose_benchmark/results/grouped-v15/ridge-weights --hamer-source <pinned-HaMeR-source> --hamer-checkpoint <hamer.ckpt> --output-dir <results>",
            "mediapipe_backend": "same external_hand_verification.py --backend mediapipe; run from an ASCII drive mapping because the native graph loader fails on this Windows installation under the Unicode workspace path",
            "aggregate": "python analysis/external_hand_verification.py --backend aggregate --output-dir <results>",
            "preview_export": "python analysis/export_occlusion_previews.py --data-root <extracted/hand_pose> --output-dir <results/occlusion_previews>",
        },
        "environments": environments,
        "artifacts": {"prediction_and_report_files": runs,
                      "training_report": {"sha256": digest(training_report),
                                          "size_bytes": training_report.stat().st_size},
                      "resource_probes": resource_probes,
                      "realtime_checkpoints": checkpoints, "masked_previews": previews},
        "preservation": "Original grouped-v15 weights and reports were not overwritten. Original source videos and labels remain outside Git; predictions, A/B checkpoints, masked previews, and the final report are committed under reports/independent_hand_verification/.",
    }
    with output.open("x", encoding="utf-8") as stream:
        json.dump(document, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "results", "models", "synthetic", "recorded", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    doc = make_provenance(**vars(args))
    print(json.dumps({"output": str(args.output), "source_files": len(doc["repository"]["source_sha256"]),
                      "videos": len(doc["datasets"]["external"]["videos"]),
                      "checkpoints": len(doc["artifacts"]["realtime_checkpoints"]),
                      "previews": len(doc["artifacts"]["masked_previews"])}))


if __name__ == "__main__":
    main()
