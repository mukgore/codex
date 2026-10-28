"""Independent Python recomputation for the local G4 actual-code run.

Reads only public source-pool landmark JSON and private run attempt/input JSON.
It does not import the JavaScript bridge or the production-code adapter and
never emits per-attempt values or source material. This is a formula cross-
check on already-known source families, not an independent holdout evaluation.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any


LANDMARK_NAMES = (
    "WRIST", "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP",
    "INDEX_MCP", "INDEX_PIP", "INDEX_DIP", "INDEX_TIP",
    "MIDDLE_MCP", "MIDDLE_PIP", "MIDDLE_DIP", "MIDDLE_TIP",
    "RING_MCP", "RING_PIP", "RING_DIP", "RING_TIP",
    "PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP",
)
ANGLE_TRIPLES = (
    (0, 5, 6), (5, 6, 7), (6, 7, 8),
    (0, 9, 10), (9, 10, 11), (10, 11, 12),
    (0, 13, 14), (13, 14, 15), (14, 15, 16),
    (0, 17, 18), (17, 18, 19), (18, 19, 20),
    (0, 1, 2), (1, 2, 3), (2, 3, 4),
)
MAX_ERROR = {"angle": 46.9413, "dtw_angle": 44.0014, "accel": 0.1926}
WEIGHTS = {"angle": 0.25, "dtw_angle": 0.38, "accel": 0.37}
SCORE_THRESHOLD = 0.25
GATE_ANGLE_THRESHOLD = 38.0
GATE_HOLD_MS = 200.0
DEFAULT_WIDTH = 720.0
DEFAULT_HEIGHT = 720.0


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"invalid {label}")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"invalid {label}")
    return value


def _load_json(path: Path) -> Any:
    def reject_constant(_: str) -> None:
        raise ValueError("non-finite JSON number")

    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def _normalise_source(data: Any) -> tuple[list[list[list[float]]], list[int]]:
    if not isinstance(data, dict) or not isinstance(data.get("frames"), list):
        raise ValueError("invalid source structure")
    info = data.get("video_info") or {}
    if not isinstance(info, dict):
        raise ValueError("invalid source metadata")
    width = _finite(info.get("width") or DEFAULT_WIDTH, "source width")
    height = _finite(info.get("height") or DEFAULT_HEIGHT, "source height")
    if width <= 0 or height <= 0:
        raise ValueError("invalid source dimensions")

    frames: list[list[list[float]]] = []
    original_indices: list[int] = []
    for fallback_index, frame in enumerate(data["frames"]):
        if not isinstance(frame, dict):
            raise ValueError("invalid source frame")
        landmarks = frame.get("landmarks_px")
        if not frame.get("detected") or landmarks is None:
            continue
        if not isinstance(landmarks, dict):
            raise ValueError("invalid source landmarks")
        normalised: list[list[float]] = []
        for name in LANDMARK_NAMES:
            point = landmarks.get(name)
            if not isinstance(point, dict):
                raise ValueError("missing source landmark")
            x = _finite(point.get("x"), "source x") / width
            y = _finite(point.get("y"), "source y") / height
            normalised.append([x, y])
        frame_index = frame.get("frame_idx", fallback_index)
        if isinstance(frame_index, bool) or not isinstance(frame_index, int) or frame_index < 0:
            raise ValueError("invalid original frame index")
        frames.append(normalised)
        original_indices.append(frame_index)
    if not frames:
        raise ValueError("source contains no detected frames")
    return frames, original_indices


def _find_keyframes(base: list[list[list[float]]]) -> list[int]:
    n = len(base)
    if n < 10:
        return [0, n // 2, n - 1]
    velocity: list[float] = []
    for i in range(1, n):
        total = 0.0
        for j in range(21):
            dx = base[i][j][0] - base[i - 1][j][0]
            dy = base[i][j][1] - base[i - 1][j][1]
            total += math.sqrt(dx * dx + dy * dy)
        velocity.append(total / 21.0)

    width = 5
    smoothed: list[float] = []
    for i in range(len(velocity)):
        lo, hi = max(0, i - width), min(len(velocity) - 1, i + width)
        smoothed.append(sum(velocity[lo : hi + 1]) / (hi - lo + 1))

    minima = [0]
    for i in range(5, len(smoothed) - 5):
        if (smoothed[i] < smoothed[i - 1]
                and smoothed[i] < smoothed[i + 1]
                and smoothed[i] < 0.005
                and i - minima[-1] > 15):
            minima.append(i)
    minima.append(n - 1)
    if len(minima) <= 4:
        return minima
    step = len(minima) // 3
    return [minima[0], minima[step], minima[step * 2], minima[-1]]


def _js_round_positive(value: float) -> int:
    # JavaScript Math.round semantics for nonnegative resampling lengths.
    return math.floor(value + 0.5)


def _segments(base: list[list[list[float]]], frames: list[dict[str, Any]]) -> list[tuple[list[list[list[float]]], list[dict[str, Any]]]]:
    indices = _find_keyframes(base)
    if len(indices) < 2 or len(base) < 2:
        raise ValueError("insufficient source frames")
    if not frames:
        raise ValueError("empty input frames")
    n_input = len(frames)
    pairs = []
    for i, end in enumerate(indices[1:]):
        start = _js_round_positive(indices[i] / (len(base) - 1) * (n_input - 1))
        stop = _js_round_positive(end / (len(base) - 1) * (n_input - 1))
        pairs.append((base[indices[i] : end + 1], frames[start : stop + 1]))
    return pairs


def _clean_input_frames(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("input must be a nonempty frame list")
    frames = []
    previous_time = None
    for frame in value:
        if not isinstance(frame, dict) or set(frame) != {"t_ms", "lm"}:
            raise ValueError("invalid input frame shape")
        timestamp = _finite(frame["t_ms"], "input timestamp")
        if previous_time is not None and timestamp <= previous_time:
            raise ValueError("input timestamps must increase")
        previous_time = timestamp
        lm = frame["lm"]
        if lm is not None:
            if not isinstance(lm, list) or len(lm) != 21:
                raise ValueError("invalid input landmarks")
            copied = []
            for point in lm:
                if not isinstance(point, list) or len(point) != 2:
                    raise ValueError("invalid input point")
                copied.append([_finite(point[0], "input x"), _finite(point[1], "input y")])
            lm = copied
        frames.append({"t_ms": timestamp, "lm": lm})
    return frames


def _angle(p1: list[float], joint: list[float], p2: list[float]) -> float:
    v1 = (p1[0] - joint[0], p1[1] - joint[1])
    v2 = (p2[0] - joint[0], p2[1] - joint[1])
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    m1 = math.sqrt(v1[0] * v1[0] + v1[1] * v1[1]) + 1e-8
    m2 = math.sqrt(v2[0] * v2[0] + v2[1] * v2[1]) + 1e-8
    return math.degrees(math.acos(max(-1.0, min(1.0, dot / (m1 * m2)))))


def _pose_normalise(frame: list[list[float]]) -> list[list[float]]:
    wrist = frame[0]
    shifted = [[p[0] - wrist[0], p[1] - wrist[1]] for p in frame]
    dx, dy = shifted[9]
    scale = max(math.sqrt(dx * dx + dy * dy), 1e-6)
    return [[p[0] / scale, p[1] / scale] for p in shifted]


def _pose_series(frames: list[list[list[float]]]) -> list[list[list[float]]] | None:
    if not frames or len(frames) < 3:
        return None
    return [_pose_normalise(frame) for frame in frames]


def _resample(sequence: list[list[list[float]]] | None, count: int) -> list[list[list[float]]] | None:
    if sequence is None or len(sequence) < 3:
        return None
    if len(sequence) == count:
        return sequence
    if count <= 1:
        raise ValueError("invalid resample count")
    output = []
    for t in range(count):
        position = t / (count - 1) * (len(sequence) - 1)
        lo = math.floor(position)
        hi = min(lo + 1, len(sequence) - 1)
        fraction = position - lo
        output.append([
            [a[0] * (1 - fraction) + b[0] * fraction,
             a[1] * (1 - fraction) + b[1] * fraction]
            for a, b in zip(sequence[lo], sequence[hi])
        ])
    return output


def _angle_mae(user: list[list[list[float]]] | None,
               base: list[list[list[float]]] | None) -> float | None:
    aligned = _resample(user, len(base)) if base is not None else None
    if aligned is None or base is None:
        return None
    total = 0.0
    for p, j, d in ANGLE_TRIPLES:
        total += sum(abs(_angle(base[i][p], base[i][j], base[i][d])
                         - _angle(aligned[i][p], aligned[i][j], aligned[i][d]))
                      for i in range(len(base))) / len(base)
    return total / len(ANGLE_TRIPLES)


def _sliding_12_angle(user: list[list[list[float]]] | None,
                      base: list[list[list[float]]] | None) -> float | None:
    if user is None or base is None or len(user) < 3 or len(base) < 3:
        return None
    resized = _resample(user, _js_round_positive(len(base) * 1.2))
    if resized is None:
        return None
    best = math.inf
    for shift in range(0, len(resized) - len(base) + 1):
        aligned = resized[shift : shift + len(base)]
        total = 0.0
        for p, j, d in ANGLE_TRIPLES:
            total += sum(abs(_angle(base[i][p], base[i][j], base[i][d])
                             - _angle(aligned[i][p], aligned[i][j], aligned[i][d]))
                          for i in range(len(base))) / len(base)
        best = min(best, total / len(ANGLE_TRIPLES))
    return best


def _acceleration_mae(user: list[list[list[float]]] | None,
                      base: list[list[list[float]]] | None) -> float | None:
    if user is None or base is None:
        return None
    aligned = _resample(user, len(base))
    if aligned is None or len(base) < 5:
        return None

    def second_difference(series: list[list[list[float]]]) -> list[float]:
        values = []
        for i in range(1, len(series) - 1):
            total = 0.0
            for j in range(1, 21):
                ax = series[i + 1][j][0] - 2 * series[i][j][0] + series[i - 1][j][0]
                ay = series[i + 1][j][1] - 2 * series[i][j][1] + series[i - 1][j][1]
                total += math.sqrt(ax * ax + ay * ay)
            values.append(total / 20.0)
        return values

    expected, observed = second_difference(base), second_difference(aligned)
    if len(expected) != len(observed):
        return None
    return sum(abs(a - b) for a, b in zip(expected, observed)) / len(expected)


def _estimate(raw: float | None, scale: float, detection_rate: float) -> float:
    if raw is None:
        return 0.0
    normalised = raw / scale if scale > 0 else 0.0
    return max(0.0, min(1.0, detection_rate * max(0.0, 1.0 - normalised)))


def _compute_score(base: list[list[list[float]]],
                   frames: list[dict[str, Any]]) -> float:
    user_all: list[list[list[float]]] = []
    base_all: list[list[list[float]]] = []
    total_frames = 0
    for base_segment, response_segment in _segments(base, frames):
        detected = [frame["lm"] for frame in response_segment if frame["lm"] is not None]
        total_frames += len(response_segment)
        if len(detected) < 3:
            continue
        user_all.extend(detected)
        base_all.extend(base_segment)

    detection_rate = len(user_all) / total_frames if total_frames else 0.0
    base_pose = _pose_series(base_all)
    user_pose = _pose_series(user_all)
    angle = dtw = accel = None
    if user_pose is not None and base_pose is not None and len(user_pose) >= 3:
        angle = _angle_mae(user_pose, base_pose)
        dtw = _sliding_12_angle(user_pose, base_pose)
        accel = _acceleration_mae(user_pose, base_pose)
    score_angle = _estimate(angle, MAX_ERROR["angle"], detection_rate)
    score_dtw = _estimate(dtw, MAX_ERROR["dtw_angle"], detection_rate)
    score_accel = _estimate(accel, MAX_ERROR["accel"], detection_rate)
    return (score_dtw * WEIGHTS["dtw_angle"]
            + score_accel * WEIGHTS["accel"]
            + score_angle * WEIGHTS["angle"])


def _gate_match_error(user: list[list[float]], target: list[list[float]]) -> float:
    user_pose, target_pose = _pose_normalise(user), _pose_normalise(target)
    return sum(abs(_angle(user_pose[p], user_pose[j], user_pose[d])
                   - _angle(target_pose[p], target_pose[j], target_pose[d]))
               for p, j, d in ANGLE_TRIPLES) / len(ANGLE_TRIPLES)


def _compute_gate(base: list[list[list[float]]], frames: list[dict[str, Any]]) -> bool:
    targets = [base[index] for index in _find_keyframes(base)]
    if not targets:
        return False
    phase = "matching"
    keyframe_index = 0
    hold_start: float | None = None
    for frame in frames:
        now = frame["t_ms"]
        landmarks = frame["lm"]
        if landmarks is None:
            hold_start = None
            continue

        # Mirror the onRes control flow: the first match changes phase to
        # recording synchronously, then the same frame can be checked against
        # the next target because video/fade scheduling is stubbed off.
        if phase == "matching" and keyframe_index < len(targets):
            error = _gate_match_error(landmarks, targets[keyframe_index])
            if error < GATE_ANGLE_THRESHOLD:
                if hold_start is None:
                    hold_start = now
                if now - hold_start >= GATE_HOLD_MS:
                    hold_start = None
                    keyframe_index += 1
                    phase = "done" if keyframe_index >= len(targets) else "recording"
            else:
                hold_start = None

        if phase == "recording" and keyframe_index < len(targets):
            error = _gate_match_error(landmarks, targets[keyframe_index])
            if error < GATE_ANGLE_THRESHOLD:
                if hold_start is None:
                    hold_start = now
                if now - hold_start >= GATE_HOLD_MS:
                    hold_start = None
                    keyframe_index += 1
                    phase = "done" if keyframe_index >= len(targets) else "recording"
            else:
                hold_start = None
    return keyframe_index == len(targets)


def _expected_result(base: list[list[list[float]]], frames: list[dict[str, Any]]) -> tuple[float, bool, bool]:
    score = _compute_score(base, frames)
    return score, score >= SCORE_THRESHOLD, _compute_gate(base, frames)


def _source_map(source_root: Path) -> dict[str, list[list[list[float]]]]:
    manifest = _load_json(source_root / "pool_manifest.json")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("clips"), list):
        raise ValueError("invalid pool manifest")
    sources: dict[str, list[list[list[float]]]] = {}
    for clip in manifest["clips"]:
        if not isinstance(clip, dict):
            raise ValueError("invalid pool entry")
        family = clip.get("clip_id")
        relative = clip.get("landmarks_file")
        if not isinstance(family, str) or not family or not isinstance(relative, str):
            raise ValueError("invalid pool entry")
        path = (source_root / relative).resolve()
        if not path.is_relative_to(source_root):
            raise ValueError("source path escapes source root")
        frames, _ = _normalise_source(_load_json(path))
        if family in sources:
            raise ValueError("duplicate source family")
        sources[family] = frames
    return sources


def _legacy_values(row: Any) -> tuple[float, bool, bool]:
    if not isinstance(row, dict):
        raise ValueError("invalid attempt row")
    legacy = row.get("legacy_result")
    if not isinstance(legacy, dict) or not isinstance(legacy.get("score"), dict):
        raise ValueError("invalid legacy result")
    score = _finite(legacy["score"].get("captcha"), "legacy score")
    score_pass = legacy.get("score_pass")
    gate_pass = legacy.get("gate_pass")
    if type(score_pass) is not bool or type(gate_pass) is not bool:
        raise ValueError("invalid legacy booleans")
    return score, score_pass, gate_pass


def verify(source_root: Path, run_dir: Path, tolerance: float) -> dict[str, Any]:
    source_root = source_root.resolve()
    run_dir = run_dir.resolve()
    if not source_root.is_dir() or not run_dir.is_dir():
        raise ValueError("source root and run directory must exist")
    sources = _source_map(source_root)
    attempts_path = run_dir / "attempts.jsonl"
    if not attempts_path.is_file():
        raise ValueError("attempts file missing")

    counts = {"score": 0, "score_pass": 0, "gate_pass": 0}
    checks = {"score": 0, "score_pass": 0, "gate_pass": 0}
    max_error = 0.0
    attempt_count = 0

    for line in attempts_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        attempt_count += 1
        row = json.loads(line, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite JSON number")))
        if not isinstance(row, dict):
            raise ValueError("invalid attempt row")
        family = row.get("source_family")
        if not isinstance(family, str) or family not in sources:
            raise ValueError("unknown source family")
        input_ref = row.get("input_ref")
        if not isinstance(input_ref, str) or not input_ref:
            raise ValueError("invalid input reference")
        input_path = (run_dir / input_ref).resolve()
        if not input_path.is_relative_to(run_dir) or not input_path.is_file():
            raise ValueError("input reference escapes run directory or is missing")
        frames = _clean_input_frames(_load_json(input_path))
        actual_score, actual_score_pass, actual_gate_pass = _expected_result(sources[family], frames)
        legacy_score, legacy_score_pass, legacy_gate_pass = _legacy_values(row)

        error = abs(actual_score - legacy_score)
        max_error = max(max_error, error)
        checks["score"] += 1
        checks["score_pass"] += 1
        checks["gate_pass"] += 1
        counts["score"] += error > tolerance
        counts["score_pass"] += actual_score_pass != legacy_score_pass
        counts["gate_pass"] += actual_gate_pass != legacy_gate_pass

    if attempt_count == 0:
        raise ValueError("attempts file contains no rows")

    return {
        "scope": "independent_python_formula_cross_check; not an independent source holdout",
        "attempt_count": attempt_count,
        "checks": checks,
        "mismatches": counts,
        "score_error_max_abs": max_error,
        "score_tolerance": tolerance,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--tolerance", type=float, default=1e-10)
    args = parser.parse_args(argv)
    if not math.isfinite(args.tolerance) or args.tolerance < 0:
        parser.error("--tolerance must be finite and nonnegative")
    try:
        summary = verify(args.source_root, args.run_dir, args.tolerance)
        output = args.run_dir.resolve() / "independent_validation.json"
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(output)
    except Exception as error:
        # Do not echo paths, input values, participant identifiers, or raw rows.
        print(f"independent check failed ({type(error).__name__})", file=sys.stderr)
        return 2
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
