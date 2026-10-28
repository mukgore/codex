"""Bounded local fault-injection check of actual Stage 6 masking behavior.

Reads only the first three frames of the existing local source clip for pixel
experiments, extracts the original Stage 6 functions with AST, and substitutes
VideoCapture/VideoWriter with bounded spies. Real local video decoding and the
real OpenCV circle rasterizer remain in use. No video output is written.

The scalar 1.95 is a test fixture only, not a calibrated weight. Results cover
this fault-injection assay only and do not establish CAPTCHA efficacy, original
deployment leakage, human usability, or held-out security performance.
"""
from __future__ import annotations

import ast
import argparse
import copy
import json
from pathlib import Path
import types
from typing import Any

import cv2
import numpy as np

from .masking import mask_video_frames, preflight_masks


SOURCE_ROOT = Path(__file__).resolve().parents[2] / "g4-handcaptcha-source"
FRAME_LIMIT = 3
W3_TEST_SCALAR = 1.95  # A test scalar only; this is not calibration evidence.


def _extract_function(path: Path, name: str) -> ast.FunctionDef:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
    matches = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {name} definition in {path.name}")
    return copy.deepcopy(matches[0])


def _load_actual_functions(source_root: Path) -> dict[str, Any]:
    # Load the source's pure constants/vector functions from this exact root,
    # avoiding a stale dataset_pipeline module from a prior source selection.
    pipeline = source_root / "dataset_pipeline"
    def load_read_only(name: str, path: Path):
        module = types.ModuleType(name)
        # Compile in memory: importlib loaders would create __pycache__ in
        # the reference source tree, contrary to its read-only role.
        exec(compile(path.read_text(encoding="utf-8"), f"<source:{name}>", "exec"), module.__dict__)
        return module
    source_common = load_read_only("g4_mask_source_common", pipeline / "common.py")
    source_geometry = load_read_only("g4_mask_source_geometry", pipeline / "geometry.py")
    stage1_path = pipeline / "stage1_extract.py"
    stage6_path = pipeline / "stage6_occlusion.py"

    namespace: dict[str, Any] = {
        "LANDMARK_NAMES": source_common.LANDMARK_NAMES,
        "P0": source_common.P0,
        "P9": source_common.P9,
        "dist": source_geometry.dist,
        "midpoint": source_geometry.midpoint,
    }
    functions = [
        (stage1_path, "frame_points"),
        (stage6_path, "project_occlusion_circle"),
        (stage6_path, "generate_occluded_video"),
    ]
    for path, name in functions:
        module = ast.Module(body=[_extract_function(path, name)], type_ignores=[])
        ast.fix_missing_locations(module)
        exec(compile(module, f"<ast:{path.name}:{name}>", "exec"), namespace)
    return namespace


def _read_first_three(source_root: Path) -> tuple[list[dict], list[np.ndarray], dict[str, float]]:
    video_path = source_root / "custom01.mp4"
    landmarks_path = source_root / "custom01_landmarks.json"
    if not video_path.is_file() or not landmarks_path.is_file():
        raise FileNotFoundError("approved local source fixture is unavailable")
    source = json.loads(landmarks_path.read_text(encoding="utf-8"))
    source_frames = source.get("frames")
    info = source.get("video_info")
    if not isinstance(source_frames, list) or len(source_frames) < FRAME_LIMIT:
        raise ValueError("source landmark fixture has fewer than three frames")
    if not isinstance(info, dict):
        raise ValueError("source landmark fixture has no video_info mapping")

    selected_frames = source_frames[:FRAME_LIMIT]
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise OSError("local source clip could not be decoded")
    images: list[np.ndarray] = []
    try:
        for _ in range(FRAME_LIMIT):
            ok, image = cap.read()
            if not ok or image is None:
                raise OSError("local source clip ended before three decoded frames")
            images.append(image.copy())
    finally:
        cap.release()

    expected_size = (int(info["height"]), int(info["width"]))
    if any(tuple(image.shape[:2]) != expected_size for image in images):
        raise ValueError("decoded dimensions differ from source landmark metadata")
    return selected_frames, images, {
        "width": float(info["width"]),
        "height": float(info["height"]),
        "fps": float(info["fps"]),
    }


class _LimitedCapture:
    def __init__(self, path: str, limit: int) -> None:
        self._capture = cv2.VideoCapture(path)
        if not self._capture.isOpened():
            raise OSError("actual Stage 6 capture spy could not open local clip")
        self.limit = limit
        self.read_count = 0
        self.originals: list[np.ndarray] = []

    def read(self):
        if self.read_count >= self.limit:
            return False, None
        ok, image = self._capture.read()
        self.read_count += 1
        if ok and image is not None:
            self.originals.append(image.copy())
        return ok, image

    def release(self) -> None:
        self._capture.release()


class _MemoryWriter:
    def __init__(self) -> None:
        self.frames: list[np.ndarray] = []
        self.released = False

    def write(self, image: np.ndarray) -> None:
        self.frames.append(image.copy())

    def release(self) -> None:
        self.released = True


class _Cv2Spy:
    """Replace only VideoCapture/VideoWriter; retain real OpenCV drawing."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.capture: _LimitedCapture | None = None
        self.writer: _MemoryWriter | None = None
        self.circle_calls = 0

    def VideoCapture(self, path: str) -> _LimitedCapture:
        self.capture = _LimitedCapture(path, self.limit)
        return self.capture

    def VideoWriter_fourcc(self, *args) -> int:
        return cv2.VideoWriter_fourcc(*args)

    def VideoWriter(self, *args, **kwargs) -> _MemoryWriter:
        self.writer = _MemoryWriter()
        return self.writer

    def circle(self, *args, **kwargs):
        self.circle_calls += 1
        return cv2.circle(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(cv2, name)


def _run_actual_loop(
    generate,
    input_frames: list[dict],
    info: dict,
    video_path: Path,
) -> dict[str, Any]:
    spy = _Cv2Spy(FRAME_LIMIT)
    # The extracted function resolves this module global at call time.
    generate.__globals__["cv2"] = spy
    generate(str(video_path), input_frames, info, W3_TEST_SCALAR, "memory-only-output")
    if spy.capture is None or spy.writer is None:
        raise RuntimeError("actual Stage 6 loop did not use the capture/writer spy")
    if not spy.capture._capture.isOpened() and spy.capture.read_count != FRAME_LIMIT:
        # A released/failed source is a mechanical error, not an attack result.
        raise RuntimeError("actual source capture did not return all three frames")
    if not spy.writer.released or len(spy.writer.frames) != FRAME_LIMIT:
        raise RuntimeError("actual Stage 6 loop did not close and write exactly three frames")
    return {
        "originals": spy.capture.originals,
        "outputs": spy.writer.frames,
        "circle_calls": spy.circle_calls,
        "capture_reads": spy.capture.read_count,
    }


def _changed_pixels(left: np.ndarray, right: np.ndarray) -> int:
    return int(np.count_nonzero(np.any(left != right, axis=2)))


def _expected_mask(image: np.ndarray, circle: tuple, *, actual_cv2=cv2) -> np.ndarray:
    center, radius = circle
    output = image.copy()
    actual_cv2.circle(
        output,
        (int(center[0]), int(center[1])),
        int(radius),
        (0, 0, 0),
        -1,
    )
    return output


def _make_missing(frame: dict) -> dict:
    altered = copy.deepcopy(frame)
    altered["detected"] = False
    return altered


def run_experiment(source_root: Path | str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run the bounded assay against the default or selected local source root."""
    source_root = Path(source_root).resolve() if source_root is not None else SOURCE_ROOT.resolve()
    video_path = source_root / "custom01.mp4"
    functions = _load_actual_functions(source_root)
    frame_points = functions["frame_points"]
    actual_project = functions["project_occlusion_circle"]
    actual_generate = functions["generate_occluded_video"]
    frames, decoded_images, video_info = _read_first_three(source_root)
    source_images_before = [image.copy() for image in decoded_images]
    if any(frame_points(frame, "px") is None for frame in frames):
        raise ValueError("the selected three-frame complete fixture contains a missing mask")

    # Source-code behavior on a complete, locally decoded three-frame fixture.
    complete_legacy = _run_actual_loop(actual_generate, frames, video_info, video_path)
    if complete_legacy["circle_calls"] != FRAME_LIMIT:
        raise AssertionError("actual source circle function did not draw on every complete frame")

    # Fault-inject absent detection metadata at the beginning and middle.
    first_missing_frames = copy.deepcopy(frames)
    first_missing_frames[0] = _make_missing(first_missing_frames[0])
    first_missing = _run_actual_loop(actual_generate, first_missing_frames, video_info, video_path)
    first_missing_unmasked = np.array_equal(
        first_missing["originals"][0], first_missing["outputs"][0]
    )
    if not first_missing_unmasked:
        raise AssertionError("first missing mask did not expose the source write behavior")

    middle_missing_frames = copy.deepcopy(frames)
    middle_missing_frames[1] = _make_missing(middle_missing_frames[1])
    middle_missing = _run_actual_loop(actual_generate, middle_missing_frames, video_info, video_path)
    previous_circle = actual_project(frame_points(frames[0], "px"), W3_TEST_SCALAR)
    expected_stale_middle = _expected_mask(middle_missing["originals"][1], previous_circle)
    stale_middle_reused = np.array_equal(
        middle_missing["outputs"][1], expected_stale_middle
    ) and _changed_pixels(
        middle_missing["originals"][1], middle_missing["outputs"][1]
    ) > 0
    if not stale_middle_reused:
        raise AssertionError("actual Stage 6 middle-missing mask reuse was not reproduced")

    # If there are fewer landmark rows than decoded video frames, Stage 6 keeps
    # the last prior circle; it does not fail the complete asset closed.
    short_frames = copy.deepcopy(frames[:2])
    short_map = _run_actual_loop(actual_generate, short_frames, video_info, video_path)
    previous_last_circle = actual_project(frame_points(frames[1], "px"), W3_TEST_SCALAR)
    expected_stale_tail = _expected_mask(short_map["originals"][2], previous_last_circle)
    stale_tail_reused = np.array_equal(short_map["outputs"][2], expected_stale_tail)
    if not stale_tail_reused:
        raise AssertionError("actual Stage 6 short-map stale-mask behavior was not reproduced")

    # Strict wrapper: complete maps are accepted, all bad maps/counts fail
    # before any rendering, and source arrays remain byte-identical.
    safe_complete = mask_video_frames(
        decoded_images, frames, w3=W3_TEST_SCALAR
    )
    wrapper_source_unchanged = all(
        np.array_equal(before, after)
        for before, after in zip(source_images_before, decoded_images)
    )
    if not wrapper_source_unchanged:
        raise AssertionError("strict wrapper changed an input source image")

    z_changed_frames = copy.deepcopy(frames)
    for frame in z_changed_frames:
        for point in frame["landmarks_px"].values():
            point["z"] += 1000.0
    safe_z_masks = preflight_masks(z_changed_frames, w3=W3_TEST_SCALAR)
    safe_original_masks = preflight_masks(frames, w3=W3_TEST_SCALAR)
    safe_z_invariant = safe_z_masks == safe_original_masks
    safe_z_images = mask_video_frames(
        decoded_images, z_changed_frames, w3=W3_TEST_SCALAR
    )
    safe_z_image_invariant = all(
        np.array_equal(left, right) for left, right in zip(safe_complete, safe_z_images)
    )
    if not (safe_z_invariant and safe_z_image_invariant):
        raise AssertionError("strict mask geometry changed when only z values changed")

    # The real Stage 6 project function uses 3D distance on pixel landmarks;
    # alter only one z component to mechanically show the dimensional coupling.
    px_points = frame_points(frames[0], "px")
    z_mutated_points = [tuple(point) for point in px_points]
    z_mutated_points[9] = (
        z_mutated_points[9][0],
        z_mutated_points[9][1],
        z_mutated_points[9][2] + 1000.0,
    )
    old_circle = actual_project(px_points, W3_TEST_SCALAR)
    old_circle_z_changed = actual_project(z_mutated_points, W3_TEST_SCALAR)
    legacy_z_changes_radius = old_circle[1] != old_circle_z_changed[1]
    if not legacy_z_changes_radius:
        raise AssertionError("actual source Stage 6 radius did not respond to z fault injection")

    # Strict wrapper fails before rendering on missing first/middle rows and a
    # source-map/decode length mismatch.
    rejected = {}
    for label, bad_frames in (
        ("missing_first", first_missing_frames),
        ("missing_middle", middle_missing_frames),
        ("length_mismatch", short_frames),
    ):
        try:
            mask_video_frames(decoded_images, bad_frames, w3=W3_TEST_SCALAR)
        except ValueError:
            rejected[label] = True
        else:
            rejected[label] = False
    if not all(rejected.values()):
        raise AssertionError(f"strict wrapper did not reject all invalid complete-asset cases: {rejected}")

    # Confirm the strict wrapper produced actual raster changes while retaining
    # the original decoded arrays unchanged.
    safe_changed_counts = [
        _changed_pixels(before, output)
        for before, output in zip(decoded_images, safe_complete)
    ]
    if not all(count > 0 for count in safe_changed_counts):
        raise AssertionError("complete strict fixture did not rasterize visible circle masks")

    summary = {
        "protocol": "bounded local Stage 6 fault-injection; first three source frames only",
        "source_fixture": "custom01 existing local source",
        "decoded_frame_count": FRAME_LIMIT,
        "w3_test_scalar": W3_TEST_SCALAR,
        "w3_is_calibration": False,
        "actual_source_function_ast_extracted": True,
        "cv2_capture_writer_replaced_with_memory_spies": True,
        "actual_video_decode_and_circle_rasterizer_used": True,
        "legacy_stage6_observations": {
            "complete_fixture_circle_calls": complete_legacy["circle_calls"],
            "missing_first_wrote_unmasked_source_frame": first_missing_unmasked,
            "missing_first_behavior_description": (
                "fault-injected decoded input frame was passed to the writer without an added Stage 6 mask; "
                "this does not mean the source video file was modified or delivered unmasked"
            ),
            "missing_middle_reused_previous_mask": stale_middle_reused,
            "short_landmark_map_reused_stale_mask_on_video_tail": stale_tail_reused,
            "z_only_change_altered_actual_stage6_radius": legacy_z_changes_radius,
        },
        "strict_wrapper_observations": {
            "complete_three_frame_fixture_accepted": True,
            "missing_first_rejected_before_any_output": rejected["missing_first"],
            "missing_middle_rejected_before_any_output": rejected["missing_middle"],
            "frame_count_mismatch_rejected_before_any_output": rejected["length_mismatch"],
            "z_only_changes_leave_2d_masks_and_output_identical": safe_z_invariant and safe_z_image_invariant,
            "decoded_source_images_unchanged": wrapper_source_unchanged,
            "masked_pixel_count_total": sum(safe_changed_counts),
        },
        "interpretation_limit": "mechanical fault-injection evidence only; not a claim about deployed assets, challenge success, security efficacy, people, or holdout generalization",
    }
    # Trace is intentionally raw-free: no frames, coordinates, scores, or hashes.
    trace = {
        "run_kind": "raw-free local masking fault-injection trace",
        "source_fixture": "custom01 existing local source",
        "decoded_frames": FRAME_LIMIT,
        "actual_source_function_ast_extracted": True,
        "fault_cases": {
            "first_mask_missing": {
                "legacy_source_frame_written_unmasked": first_missing_unmasked,
                "legacy_behavior_description": (
                    "input frame passed to writer without an added Stage 6 mask; "
                    "not evidence of source-file modification or unmasked delivery"
                ),
                "strict_wrapper_rejected_asset": rejected["missing_first"],
            },
            "middle_mask_missing": {
                "legacy_previous_mask_reused": stale_middle_reused,
                "strict_wrapper_rejected_asset": rejected["missing_middle"],
            },
            "landmark_rows_shorter_than_decoded_video": {
                "legacy_stale_mask_reused_on_tail": stale_tail_reused,
                "strict_wrapper_rejected_asset": rejected["length_mismatch"],
            },
            "z_only_fault": {
                "legacy_radius_changed": legacy_z_changes_radius,
                "strict_2d_mask_unchanged": safe_z_invariant,
            },
        },
        "source_images_unchanged_by_strict_wrapper": wrapper_source_unchanged,
        "w3_test_scalar": W3_TEST_SCALAR,
        "w3_is_calibration": False,
        "contains_raw_frames_coordinates_or_hashes": False,
        "claim_limit": summary["interpretation_limit"],
    }
    return summary, trace


def _write_new_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Preserve any prior output; this run never silently overwrites a record.
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the bounded, local Stage 6 mask fault-injection assay."
    )
    repo = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--source-root",
        type=Path,
        default=SOURCE_ROOT,
        help="local source checkout containing custom01.mp4 and its landmark JSON",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=repo / "data" / "work" / "g4_actual_run",
        help="new private run directory; raw-free mask_validation.json is written here",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=repo / "reports" / "g4_actual" / "mask_summary.json",
        help="new aggregate JSON summary path",
    )
    args = parser.parse_args()
    summary_path = args.output
    trace_path = args.run_dir / "mask_validation.json"
    if summary_path.resolve() == trace_path.resolve():
        parser.error("--output and --run-dir/mask_validation.json must be different paths")
    if summary_path.exists() or trace_path.exists():
        raise FileExistsError("mask experiment output already exists; refusing to overwrite")
    summary, trace = run_experiment(args.source_root)
    _write_new_json(summary_path, summary)
    _write_new_json(trace_path, trace)
    print(json.dumps({
        "summary_written": str(summary_path),
        "private_trace_written": str(trace_path),
        "legacy_missing_first_unmasked": summary["legacy_stage6_observations"]["missing_first_wrote_unmasked_source_frame"],
        "legacy_middle_stale_reused": summary["legacy_stage6_observations"]["missing_middle_reused_previous_mask"],
        "strict_wrapper_rejections": summary["strict_wrapper_observations"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
