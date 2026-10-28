"""Aggregate-only independent formula check for the legacy supplement."""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys

from .independent_check import (
    _expected_result,
    _load_json,
    _normalise_source,
)


def _resample(series, count):
    if not series or count < 1:
        raise ValueError("invalid resample input")
    if len(series) == count:
        return [[point[:] for point in frame] for frame in series]
    if count == 1:
        return [[point[:] for point in series[0]]]
    out = []
    for i in range(count):
        pos = i * (len(series) - 1) / (count - 1)
        lo = math.floor(pos)
        hi = min(lo + 1, len(series) - 1)
        frac = pos - lo
        out.append([
            [a[0] * (1 - frac) + b[0] * frac,
             a[1] * (1 - frac) + b[1] * frac]
            for a, b in zip(series[lo], series[hi])
        ])
    return out


def _records(source_root):
    raw = _load_json(source_root / "landmarks_base.json")
    if not isinstance(raw, dict) or len(raw) != 6:
        raise ValueError("unexpected legacy record collection")
    for data in raw.values():
        normalized, orig_idx = _normalise_source(data)
        fps = float(data["video_info"]["fps"])
        if not math.isfinite(fps) or fps <= 0:
            raise ValueError("invalid legacy fps")
        yield normalized, orig_idx, fps


def _inputs(base, orig_idx, fps, foreign):
    n = len(base)
    if n == 0 or len(orig_idx) != n:
        raise ValueError("invalid normalized source")
    first = base[0]
    last = base[-1]
    interpolation = []
    for i in range(n):
        fraction = i / max(1, n - 1)
        interpolation.append([
            [a[0] * (1 - fraction) + b[0] * fraction,
             a[1] * (1 - fraction) + b[1] * fraction]
            for a, b in zip(first, last)
        ])
    methods = {
        "exact_replay": base,
        "hold_first": [first for _ in range(n)],
        "endpoint_interpolation": interpolation,
        "fixed_current_pool_reference": _resample(foreign, n),
    }
    return {
        name: [
            {"t_ms": orig_idx[i] * 1000 / fps,
             "lm": [[float(x), float(y)] for x, y in frame]}
            for i, frame in enumerate(array)
        ]
        for name, array in methods.items()
    }


def verify(source_root: Path, run_dir: Path, summary_path: Path, output: Path, tolerance=1e-10):
    source_root, run_dir, summary_path, output = (
        source_root.resolve(), run_dir.resolve(), summary_path.resolve(), output.resolve()
    )
    if not source_root.is_dir() or not run_dir.is_dir():
        raise ValueError("source and run directories must exist")
    summary = _load_json(summary_path)
    result_rows = _load_json(run_dir / "results.json")
    if summary.get("run_id") != "G4-LEGACY-SUPPLEMENT-001" or len(result_rows) != 24:
        raise ValueError("unexpected supplement result set")

    current_manifest = _load_json(source_root / "pool_manifest.json")
    current_sources = {}
    for clip in current_manifest["clips"]:
        family = clip["clip_id"]
        data = _load_json((source_root / clip["landmarks_file"]).resolve())
        current_sources[family] = _normalise_source(data)[0]
    if not current_sources:
        raise ValueError("empty current source pool")
    foreign = current_sources[sorted(current_sources)[0]]

    expected = {}
    for record_index, (base, orig_idx, fps) in enumerate(_records(source_root), 1):
        for attack_id, frames in _inputs(base, orig_idx, fps, foreign).items():
            expected[(record_index, attack_id)] = _expected_result(base, frames)
    if len(expected) != 24:
        raise ValueError("unexpected reconstructed input count")

    mismatches = {"score": 0, "score_pass": 0, "gate_pass": 0}
    max_error = 0.0
    for row in result_rows:
        key = (row.get("legacy_record"), row.get("attack_id"))
        if key not in expected:
            raise ValueError("unknown result row")
        score, score_pass, gate_pass = expected.pop(key)
        actual = row.get("result") or {}
        actual_score = float(actual["score"]["captcha"])
        error = abs(score - actual_score)
        max_error = max(max_error, error)
        mismatches["score"] += error > tolerance
        mismatches["score_pass"] += score_pass != actual.get("score_pass")
        mismatches["gate_pass"] += gate_pass != actual.get("gate_pass")
    if expected:
        raise ValueError("incomplete result set")

    report = {
        "scope": "independent Python formula cross-check; legacy records are not an independent holdout",
        "attempt_count": 24,
        "source_records": 6,
        "attack_conditions": 4,
        "checks": {"score": 24, "score_pass": 24, "gate_pass": 24},
        "mismatches": mismatches,
        "score_error_max_abs": max_error,
        "score_tolerance": tolerance,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = verify(args.source_root, args.run_dir, args.summary, args.output)
    except Exception as exc:
        print(f"independent legacy check failed ({type(exc).__name__})", file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
