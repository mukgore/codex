"""Local-only A2 metadata and bounded circle-contour probe for G4.

Reads only the approved source copy's pool_manifest.json and its eight
manifest-listed video_file MP4s. It does not inspect landmark JSON, human
records, external services, browsers, or any other source files. Metadata
features are development/exploratory diagnostics, not independent holdout
evidence. Exact filename-to-clip lookup is separately reported as directly
exposed metadata when filenames are visible.

The optional contour probe follows the existing local stage12_extract.py
definition: grayscale, inverse threshold at 15, largest external contour,
area >= 200, then minEnclosingCircle. At most 30 evenly spaced frames per
clip are probed. Without independent per-frame circle ground truth, successful
contour detections are not evidence of circle-only attack success.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import cv2
import numpy as np


LAB_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = LAB_ROOT.parent / "g4-handcaptcha-source"
DEFAULT_RUN_DIR = LAB_ROOT / "data" / "work" / "g4_actual_run"
DEFAULT_OUTPUT = LAB_ROOT / "reports" / "g4_actual" / "pixel_summary.json"
MAX_CIRCLE_SAMPLES_PER_CLIP = 30


def _detect_circle(frame: np.ndarray) -> dict[str, float | int] | None:
    """Replicate the documented stage12_extract contour-circle primitive."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, threshold = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(
        threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    area = float(cv2.contourArea(contour))
    if area < 200:
        return None
    (cx, cy), radius = cv2.minEnclosingCircle(contour)
    h, w = frame.shape[:2]
    if not (0 <= cx < w and 0 <= cy < h and radius > 0):
        return None
    return {
        "center_x_px": float(cx),
        "center_y_px": float(cy),
        "radius_px": float(radius),
        "contour_area_px2": area,
    }


def _analyze_clip(clip: dict[str, object], source_root: Path) -> dict[str, object]:
    video_name = str(clip["video_file"])
    video_path = (source_root / video_name).resolve()
    if video_path.parent != source_root.resolve():
        raise ValueError("manifest video_file must resolve inside source root")
    if not video_path.is_file():
        raise FileNotFoundError(f"manifest-listed MP4 is missing: {video_name}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        cap.release()
        raise RuntimeError(f"OpenCV could not open manifest-listed MP4: {video_name}")

    reported_frames = int(round(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    width = int(round(cap.get(cv2.CAP_PROP_FRAME_WIDTH)))
    height = int(round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    sample_indices = set(
        int(i)
        for i in np.unique(
            np.linspace(
                0,
                max(0, reported_frames - 1),
                min(MAX_CIRCLE_SAMPLES_PER_CLIP, max(1, reported_frames)),
                dtype=np.int64,
            )
        )
    )

    decoded_frames = 0
    sampled_features: list[dict[str, object]] = []
    decoded_width = decoded_height = None
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        h, w = frame.shape[:2]
        if decoded_frames == 0:
            decoded_width, decoded_height = int(w), int(h)
        if decoded_frames in sample_indices:
            detection = _detect_circle(frame)
            sampled_features.append(
                {
                    "frame_index_zero_based": decoded_frames,
                    "status": "contour_candidate" if detection else "no_contour_candidate",
                    "circle_candidate": detection,
                }
            )
        decoded_frames += 1
    cap.release()

    manifest_frames = int(clip["n_frames"])
    manifest_fps = float(clip["fps"])
    count_match = decoded_frames == manifest_frames
    metadata_count_match = reported_frames == manifest_frames
    fps_match = bool(np.isclose(fps, manifest_fps, rtol=1e-3, atol=1e-3))

    return {
        "clip_id": str(clip["clip_id"]),
        "video_file": video_name,
        "file_size_bytes": int(video_path.stat().st_size),
        "manifest": {"n_frames": manifest_frames, "fps": manifest_fps},
        "opencv_video_metadata": {
            "reported_frame_count": reported_frames,
            "fps": fps,
            "width_px": width,
            "height_px": height,
        },
        "full_decode": {
            "decoded_frame_count": decoded_frames,
            "first_decoded_frame_width_px": decoded_width,
            "first_decoded_frame_height_px": decoded_height,
            "manifest_n_frames_matches_decoded": count_match,
            "opencv_reported_count_matches_manifest": metadata_count_match,
            "manifest_fps_matches_opencv_metadata": fps_match,
            "dimensions_match_decoded_frame": bool(
                decoded_width == width and decoded_height == height
            ),
        },
        "circle_contour_probe": {
            "method": "stage12_extract detect_circle equivalent",
            "max_sample_frames": MAX_CIRCLE_SAMPLES_PER_CLIP,
            "sampled_frame_count": len(sampled_features),
            "ground_truth_available": False,
            "interpretation": "candidate detections only; not circle-only attack success",
            "sampled_frames": sampled_features,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-root", type=Path, default=DEFAULT_SOURCE_ROOT,
        help="Read-only source copy containing pool_manifest.json and its MP4s.",
    )
    parser.add_argument(
        "--run-dir", type=Path, default=DEFAULT_RUN_DIR,
        help="Directory for private pixel_features.json output.",
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help="Path for the nonidentifying aggregate summary JSON.",
    )
    args = parser.parse_args()
    source_root = args.source_root.expanduser().resolve()
    run_dir = args.run_dir.expanduser().resolve()
    raw_path = run_dir / "pixel_features.json"
    summary_path = args.output.expanduser().resolve()

    # Refuse to overwrite anything, including a prior run's independent output.
    if raw_path.exists() or summary_path.exists():
        raise FileExistsError("refusing to overwrite existing pixel ablation output")

    manifest = json.loads((source_root / "pool_manifest.json").read_text(encoding="utf-8-sig"))
    clips = manifest.get("clips")
    if not isinstance(clips, list) or len(clips) != 8:
        raise ValueError("expected exactly eight manifest-listed clip records")
    required = {"clip_id", "video_file", "n_frames", "fps"}
    if any(not isinstance(c, dict) or not required.issubset(c) for c in clips):
        raise ValueError("pool manifest clip record is missing required fields")

    results = [_analyze_clip(clip, source_root) for clip in clips]
    decoded_counts = [int(r["full_decode"]["decoded_frame_count"]) for r in results]
    count_freq = Counter(decoded_counts)
    candidate_sizes = Counter(count_freq[n] for n in decoded_counts)
    unique_frame_count_clips = sum(count_freq[n] == 1 for n in decoded_counts)
    contour_detected = [
        len(
            [
                sample
                for sample in r["circle_contour_probe"]["sampled_frames"]
                if sample["status"] == "contour_candidate"
            ]
        )
        for r in results
    ]

    summary = {
        "scope": "local authorized A2 metadata probe; exploratory closed set",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": "b4d96d1",
        "clip_count": len(results),
        "all_manifest_video_files_resolved_by_exact_filename": True,
        "filename_channel": {
            "manifest_exact_filename_lookup_possible_count": len(results),
            "interpretation": "If filenames are observable, manifest names directly identify clip IDs; this is exposed metadata, not evidence of a robust visual inference attack.",
        },
        "frame_count_channel": {
            "basis": "full sequential OpenCV decode count",
            "all_decoded_counts_match_manifest_n_frames": all(
                r["full_decode"]["manifest_n_frames_matches_decoded"] for r in results
            ),
            "all_opencv_reported_counts_match_manifest_n_frames": all(
                r["full_decode"]["opencv_reported_count_matches_manifest"]
                for r in results
            ),
            "all_opencv_fps_match_manifest": all(
                r["full_decode"]["manifest_fps_matches_opencv_metadata"]
                for r in results
            ),
            "all_opencv_dimensions_match_decoded_frames": all(
                r["full_decode"]["dimensions_match_decoded_frame"] for r in results
            ),
            "frame_count_value_frequency": {
                str(k): int(v) for k, v in sorted(count_freq.items())
            },
            "candidate_set_size_frequency": {
                str(k): int(v) for k, v in sorted(candidate_sizes.items())
            },
            "unique_identifiable_clip_count_from_frame_count_alone": int(
                unique_frame_count_clips
            ),
            "closed_set_unique_identification_rate": (
                float(unique_frame_count_clips / len(results)) if results else None
            ),
            "interpretation": "Candidate set is the clips sharing the observed decoded frame count; this is descriptive for the eight known clips only.",
        },
        "circle_contour_probe": {
            "sample_cap_per_clip": MAX_CIRCLE_SAMPLES_PER_CLIP,
            "sampled_frames_total": int(
                sum(r["circle_contour_probe"]["sampled_frame_count"] for r in results)
            ),
            "contour_candidate_frames_total": int(sum(contour_detected)),
            "ground_truth_available": False,
            "status": "exploratory candidate extraction only; no circle-only success claim",
        },
        "nonidentifying_note": "Per-clip names and raw measurements are only in the local raw output.",
    }

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        json.dumps(
            {
                "scope": "local authorized A2 metadata probe; not held-out evaluation",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "opencv_version": cv2.__version__,
                "manifest_clip_records": results,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
