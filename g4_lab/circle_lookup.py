"""Closed-set circle-only lookup against the approved public baseline library.

Reads only pool_manifest.json, its eight manifest-listed public baseline
landmark JSON files, and this lab's pixel_features.json. Circle reference
trajectories reproduce handtest1.py's legacyformula at q=1.95 for
MIDDLE_DIP: wrist plus the mean of MCP indices [1,5,9,13,17], the midpoint
between wrist and the q-scaled MCP target, and integer radius
int(base_distance*q/2). Observed query circles are the bounded contour
candidates already extracted from actual MP4 pixels (at most 30 per clip).

All coordinates and radii are normalized on x/width and y/height axes. Each
sequence is linearly interpolated on a fixed 32-point phase grid. The fixed
distance is mean squared L2 across jointly observed phase points. No model
training, tuning, retries, or holdout selection occurs. This is an exploratory
eight-source closed-set lookup with an exposed reference library, not a claim
of unseen-source generalization or verified circle-only attack success.

For each scored prediction, ActualEvaluator replays the matched library source's
full landmark trajectory against the target source's local scoring/gate
functions. This offline assay is not a browser,
trusted camera, server endpoint, or L3 authentication test.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np

try:
    from .actual import ActualEvaluator
except ImportError:  # direct-script invocation
    from actual import ActualEvaluator

LAB_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = LAB_ROOT.parent / "g4-handcaptcha-source"
DEFAULT_RUN_DIR = LAB_ROOT / "data" / "work" / "g4_actual_run"
DEFAULT_PIXEL_FEATURES = DEFAULT_RUN_DIR / "pixel_features.json"
DEFAULT_OUTPUT = LAB_ROOT / "reports" / "g4_actual" / "circle_summary.json"
LEGACY_Q = 1.95
PHASE_POINTS = 32
TIE_RTOL = 1e-12
TIE_ATOL = 1e-15
MCP_INDICES = (1, 5, 9, 13, 17)
LANDMARK_NAMES = (
    "WRIST", "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP",
    "INDEX_MCP", "INDEX_PIP", "INDEX_DIP", "INDEX_TIP", "MIDDLE_MCP",
    "MIDDLE_PIP", "MIDDLE_DIP", "MIDDLE_TIP", "RING_MCP", "RING_PIP",
    "RING_DIP", "RING_TIP", "PINKY_MCP", "PINKY_PIP", "PINKY_DIP",
    "PINKY_TIP",
)


def _legacy_circle(frame: dict[str, object], width: float, height: float):
    if not frame.get("detected"):
        return None
    landmarks = frame.get("landmarks_px")
    if not isinstance(landmarks, dict):
        return None
    needed = [LANDMARK_NAMES[i] for i in (0, *MCP_INDICES)]
    if any(name not in landmarks for name in needed):
        return None
    try:
        wrist = np.array(
            [landmarks["WRIST"]["x"], landmarks["WRIST"]["y"]], dtype=float
        )
        mcps = np.array(
            [[landmarks[LANDMARK_NAMES[i]]["x"], landmarks[LANDMARK_NAMES[i]]["y"]]
             for i in MCP_INDICES],
            dtype=float,
        )
    except (KeyError, TypeError, ValueError):
        return None
    if not np.isfinite(wrist).all() or not np.isfinite(mcps).all():
        return None

    mcp_mean = mcps.mean(axis=0)
    base_distance = float(np.linalg.norm(mcp_mean - wrist))
    radius_px = int(base_distance * LEGACY_Q / 2.0)
    virtual_target = wrist + (mcp_mean - wrist) * LEGACY_Q
    center_px = ((wrist + virtual_target) / 2.0).astype(int)
    return np.array(
        [center_px[0] / width, center_px[1] / height,
         radius_px / width, radius_px / height],
        dtype=float,
    )


def _phase32(phases: list[float], values: list[list[float]]):
    """Interpolate observed rows only; leave uncovered phase endpoints missing."""
    p = np.asarray(phases, dtype=float)
    v = np.asarray(values, dtype=float)
    grid = np.linspace(0.0, 1.0, PHASE_POINTS)
    if len(p) < 2 or len(np.unique(p)) < 2:
        return grid, np.full((PHASE_POINTS, 4), np.nan), {
            "valid_observations": int(len(p)),
            "observed_phase_min": float(np.min(p)) if len(p) else None,
            "observed_phase_max": float(np.max(p)) if len(p) else None,
            "interpolated_grid_points": 0,
        }
    order = np.argsort(p, kind="stable")
    p, v = p[order], v[order]
    unique_p, first = np.unique(p, return_index=True)
    v = v[first]
    out = np.full((PHASE_POINTS, 4), np.nan)
    valid = (grid >= unique_p[0]) & (grid <= unique_p[-1])
    for col in range(4):
        out[valid, col] = np.interp(grid[valid], unique_p, v[:, col])
    return grid, out, {
        "valid_observations": int(len(unique_p)),
        "observed_phase_min": float(unique_p[0]),
        "observed_phase_max": float(unique_p[-1]),
        "interpolated_grid_points": int(valid.sum()),
    }


def _load_reference(clip: dict[str, object], source_root: Path):
    name = str(clip["landmarks_file"])
    path = (source_root / name).resolve()
    if path.parent != source_root.resolve() or not path.is_file():
        raise ValueError("landmarks_file must resolve to a baseline file in source root")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    info = data["video_info"]
    width, height = float(info["width"]), float(info["height"])
    n_frames = len(data["frames"])
    phases, values, raw_lm = [], [], []
    for i, frame in enumerate(data["frames"]):
        circle = _legacy_circle(frame, width, height)
        idx = int(frame.get("frame_idx", i))
        if circle is not None:
            phase = idx / max(1, n_frames - 1)
            phases.append(float(phase))
            values.append(circle.tolist())
        # Preserve the full, public, normalized sequence for optional offline
        # ActualEvaluator scoring, including explicit null detection frames.
        lm = frame.get("landmarks_px") if frame.get("detected") else None
        if isinstance(lm, dict):
            try:
                row = [[float(lm[n]["x"]) / width, float(lm[n]["y"]) / height]
                       for n in LANDMARK_NAMES]
                if not np.isfinite(np.asarray(row)).all():
                    row = None
            except (KeyError, TypeError, ValueError):
                row = None
        else:
            row = None
        raw_lm.append({
            "t_ms": idx * 1000.0 / float(info["fps"]),
            "lm": row,
        })
    _, grid_values, cov = _phase32(phases, values)
    return {
        "clip_id": str(clip["clip_id"]),
        "video_file": str(clip["video_file"]),
        "frame_count": n_frames,
        "width_px": int(width),
        "height_px": int(height),
        "fps": float(info["fps"]),
        "circle_phases": phases,
        "circle_features_normalized": values,
        "phase32": grid_values,
        "phase32_coverage": cov,
        "full_lm_frames": raw_lm,
    }


def _query_observations(record: dict[str, object]):
    info = record["opencv_video_metadata"]
    full = record["full_decode"]
    n_frames = int(full["decoded_frame_count"])
    width, height = float(info["width_px"]), float(info["height_px"])
    phases, values = [], []
    total_samples = 0
    for sample in record["circle_contour_probe"]["sampled_frames"]:
        total_samples += 1
        feature = sample.get("circle_candidate")
        if not isinstance(feature, dict):
            continue
        idx = int(sample["frame_index_zero_based"])
        phases.append(idx / max(1, n_frames - 1))
        values.append([
            float(feature["center_x_px"]) / width,
            float(feature["center_y_px"]) / height,
            float(feature["radius_px"]) / width,
            float(feature["radius_px"]) / height,
        ])
    _, grid_values, cov = _phase32(phases, values)
    return grid_values, {
        **cov,
        "total_contour_samples": int(total_samples),
        "valid_circle_observations": len(values),
        "missing_circle_observations": total_samples - len(values),
        "observation_coverage": (
            float(len(values) / total_samples) if total_samples else 0.0
        ),
    }


def _distance(query: np.ndarray, reference: np.ndarray):
    common = np.isfinite(query).all(axis=1) & np.isfinite(reference).all(axis=1)
    n = int(common.sum())
    if n == 0:
        return None, 0
    delta = query[common] - reference[common]
    return float(np.mean(np.sum(delta * delta, axis=1))), n


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root", type=Path, default=DEFAULT_SOURCE_ROOT,
        help="Read-only source copy containing the manifest and baseline landmarks.",
    )
    parser.add_argument(
        "--run-dir", type=Path, default=DEFAULT_RUN_DIR,
        help="Directory containing pixel_features.json and receiving circle_lookup.json.",
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help="Path for the aggregate circle lookup summary JSON.",
    )
    parser.add_argument(
        "--pixel-features", type=Path, default=None,
        help="Optional pixel_features.json path (default: <run-dir>/pixel_features.json).",
    )
    args = parser.parse_args()
    source_root = args.source_root.expanduser().resolve()
    run_dir = args.run_dir.expanduser().resolve()
    pixel_path = (args.pixel_features or (run_dir / "pixel_features.json")).expanduser().resolve()
    raw_path = run_dir / "circle_lookup.json"
    summary_path = args.output.expanduser().resolve()

    if raw_path.exists() or summary_path.exists():
        raise FileExistsError("refusing to overwrite an existing circle lookup output")
    manifest = json.loads((source_root / "pool_manifest.json").read_text(encoding="utf-8-sig"))
    clips = manifest.get("clips")
    pixel_doc = json.loads(pixel_path.read_text(encoding="utf-8"))
    pixel_records = pixel_doc["manifest_clip_records"]
    if not isinstance(clips, list) or len(clips) != 8 or len(pixel_records) != 8:
        raise ValueError("expected eight manifest and matching pixel feature records")

    manifest_by_id = {str(c["clip_id"]): c for c in clips}
    pixels_by_id = {str(r["clip_id"]): r for r in pixel_records}
    if set(manifest_by_id) != set(pixels_by_id):
        raise ValueError("pixel records and manifest clip IDs do not match")

    references = {
        cid: _load_reference(c, source_root) for cid, c in manifest_by_id.items()
    }
    phase32 = np.linspace(0.0, 1.0, PHASE_POINTS)
    lookup_rows = []
    actual_rows = []
    with ActualEvaluator(source_root) as evaluator:
        for target_id, pixel_record in pixels_by_id.items():
            query, qcov = _query_observations(pixel_record)
            distances = []
            for ref_id, ref in references.items():
                score, overlap = _distance(query, ref["phase32"])
                distances.append({
                    "reference_clip_id": ref_id,
                    "mean_squared_l2": score,
                    "overlapping_phase_points": overlap,
                    "status": "scored" if score is not None else "insufficient_overlap",
                })
            scored = [d for d in distances if d["mean_squared_l2"] is not None]
            scored.sort(key=lambda d: (d["mean_squared_l2"], d["reference_clip_id"]))
            if scored:
                best = float(scored[0]["mean_squared_l2"])
                tied = [d for d in scored if np.isclose(
                    float(d["mean_squared_l2"]), best, rtol=TIE_RTOL, atol=TIE_ATOL
                )]
                predicted = str(scored[0]["reference_clip_id"])
                correct = target_id == predicted
                tie_contains_correct = any(
                    d["reference_clip_id"] == target_id for d in tied
                )
                rank = next(
                    (i + 1 for i, d in enumerate(scored)
                     if d["reference_clip_id"] == target_id),
                    None,
                )
            else:
                tied, predicted, correct, tie_contains_correct, rank = [], None, False, False, None

            lookup_rows.append({
                "target_clip_id": target_id,
                "query_source": "pixel_features circle contour candidates only",
                "query_coverage": qcov,
                "ranked_reference_candidates": scored,
                "unscored_reference_candidates": [
                    d["reference_clip_id"] for d in distances
                    if d["mean_squared_l2"] is None
                ],
                "nearest_prediction": predicted,
                "nearest_correct": bool(correct),
                "nearest_tie_count": len(tied),
                "nearest_tie_clip_ids": [d["reference_clip_id"] for d in tied],
                "correct_reference_rank": rank,
                "correct_in_nearest_tie": bool(tie_contains_correct),
            })

            if predicted is not None:
                # Use the matched public baseline's full normalized landmarks
                # as an explicit library-lookup response; evaluate offline
                # against the target source without browser/server submission.
                predicted_frames = references[predicted]["full_lm_frames"]
                result = evaluator.evaluate(target_id, predicted_frames)
                actual_rows.append({
                    "target_clip_id": target_id,
                    "predicted_library_clip_id": predicted,
                    "prediction_correct": bool(predicted == target_id),
                    "score": result.get("score"),
                    "score_pass": bool(result.get("score_pass")),
                    "gate_pass": bool(result.get("gate_pass")),
                    "gate_matches": result.get("gate_matches"),
                    "gate_total": result.get("gate_total"),
                    "score_scope": result.get("score_scope"),
                    "gate_scope": result.get("gate_scope"),
                    "l3_status": "NOT_TESTED; local ActualEvaluator only",
                })
            else:
                actual_rows.append({
                    "target_clip_id": target_id,
                    "status": "not_run; no scored circle lookup candidate",
                    "l3_status": "NOT_TESTED",
                })

    n = len(lookup_rows)
    top1 = sum(r["nearest_correct"] for r in lookup_rows)
    tie_correct = sum(r["correct_in_nearest_tie"] for r in lookup_rows)
    tie_counts = Counter(r["nearest_tie_count"] for r in lookup_rows)
    score_passes = sum(r.get("score_pass", False) for r in actual_rows)
    gate_passes = sum(r.get("gate_pass", False) for r in actual_rows)
    summary = {
        "scope": "exploratory circle-only metadata lookup; eight-source closed set",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": "b4d96d1",
        "reference_knowledge": "all eight public baseline landmark sequences were used to build the candidate library; evaluation source families are not held out",
        "query_knowledge": "only normalized cx, cy, rx, ry from up to 30 actual-MP4 contour candidates per target; candidate missingness retained",
        "circle_reference_formula": "handtest1.py occlusion_params, q=1.95 for MIDDLE_DIP; verified indices/formula read-only",
        "distance": "fixed mean squared L2 over common finite rows on a fixed 32-point phase grid with linear interpolation; no tuning",
        "lookup": {
            "targets": n,
            "top1_correct_count": int(top1),
            "top1_tie_count_gt1": int(sum(r["nearest_tie_count"] > 1 for r in lookup_rows)),
            "correct_in_nearest_tie_count": int(tie_correct),
            "nearest_tie_size_frequency": {str(k): int(v) for k, v in sorted(tie_counts.items())},
            "targets_with_scored_lookup": int(sum(r["nearest_prediction"] is not None for r in lookup_rows)),
            "interpretation": "closed-set descriptive lookup only; contour center/radius accuracy has no independent per-frame ground truth",
        },
        "actual_evaluator_replay": {
            "attempts": int(len(actual_rows)),
            "actual_score_pass_count": int(score_passes),
            "actual_onres_gate_pass_count": int(gate_passes),
            "l3_counted_as_tested": 0,
            "scope": "full matched public-library landmark trajectory replayed offline against target keyframes through ActualEvaluator; not a two-clip browser session or trusted camera proof",
        },
        "data_limitations": [
            "All eight evaluation sources are also present in the public reference library; no independent holdout.",
            "Contour candidates are derived from at most 30 frames per clip and may be missing or inaccurate.",
            "No independent per-frame circle center/radius ground truth was available, so extraction accuracy and circle-only attack efficacy are unverified.",
            "ActualEvaluator score/gate are offline computations; no server protected-action endpoint was tested and L3 remains NOT_TESTED.",
        ],
    }

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        json.dumps({
            "scope": "local private exploratory lookup; not held-out evaluation",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "q": LEGACY_Q,
            "phase_points": PHASE_POINTS,
            "tie_rtol": TIE_RTOL,
            "tie_atol": TIE_ATOL,
            "reference_library": {
                cid: {
                    "formula_valid_circle_count": len(ref["circle_features_normalized"]),
                    "phase32_coverage": ref["phase32_coverage"],
                    "circle_phases": ref["circle_phases"],
                    "circle_features_normalized": ref["circle_features_normalized"],
                }
                for cid, ref in references.items()
            },
            "lookup_rows": lookup_rows,
            "actual_evaluator_rows": actual_rows,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
