"""Compare fixed raw score features on published coordinate controls, without fitting."""
import argparse
import json
from pathlib import Path
import platform
from statistics import median
import subprocess

import numpy as np

from analysis.camera_controls import adapted, diagnostics
from g4_lab.actual import ActualEvaluator
from g4_lab.attacks import generate_attacks
from g4_lab.run import resample
from validation_v03.adapters import InputSpec


CONDITIONS = ('exact_replay', 'forward_time_warp', 'hold_first', 'hold_middle', 'hold_last',
              'endpoint_interpolation', 'reverse')


def summarize(rows):
    summary = {}
    for name, pairs in rows.items():
        outcomes = [trial for _, _, trial in pairs]
        features = {}
        worse_than_warp = {}
        for positive, warped, trial in pairs:
            candidate = trial['complete_trial_candidate_features']
            reference = positive['complete_trial_candidate_features']
            if candidate is None or reference is None:
                continue
            for feature, value in candidate.items():
                features.setdefault(feature, []).append(value - reference[feature])
                warp_features = warped['complete_trial_candidate_features']
                if warp_features is not None:
                    worse_than_warp.setdefault(feature, []).append(value > warp_features[feature] + 1e-9)
        summary[name] = {
            'attempts': len(pairs),
            'legacy_score_pass': sum(trial['legacy_score_pass'] for trial in outcomes),
            'offline_gate_pass': sum(trial['offline_gate_pass'] for trial in outcomes),
            'both_pass': sum(trial['legacy_score_pass'] and trial['offline_gate_pass']
                             for trial in outcomes),
            'legacy_score_median': median(trial['legacy_score'] for trial in outcomes),
            'legacy_score_lower_than_exact': sum(
                trial['legacy_score'] < positive['legacy_score'] - 1e-9
                for positive, _, trial in pairs),
            'legacy_score_lower_than_warp': sum(
                trial['legacy_score'] < warped['legacy_score'] - 1e-9
                for _, warped, trial in pairs),
            'candidate_error_higher_than_warp': {
                feature: {'higher': sum(results), 'pairs': len(results)}
                for feature, results in worse_than_warp.items()
            },
            'complete_feature_pairs': sum(
                positive['complete_trial_candidate_features'] is not None
                and trial['complete_trial_candidate_features'] is not None
                for positive, _, trial in pairs),
            'candidate_error_delta_from_exact': {
                feature: {'median': median(deltas), 'min': min(deltas), 'max': max(deltas),
                          'positive_over_1e-9': sum(delta > 1e-9 for delta in deltas)}
                for feature, deltas in features.items()
            },
        }
    return summary


def compare(root):
    rows = {name: [] for name in (*CONDITIONS, 'wrong_library', 'middle_frame_missing')}
    with ActualEvaluator(root) as evaluator:
        for key, source in evaluator.sources.items():
            path = (root / evaluator.clips[key]['landmarks_file']).resolve()
            info = json.loads(path.read_text(encoding='utf-8'))['video_info']
            fps = info['fps']
            spec = InputSpec(info['width'], info['height'], 'normalized_xy', 'ms', False, 2 / fps)
            raw = np.asarray([frame['lm'] for frame in source['raw_frames'] if frame['lm'] is not None])
            timestamps = [frame['t_ms'] for frame in source['raw_frames'] if frame['lm'] is not None]
            if len(raw) != len(source['raw_frames']):
                raise ValueError('Fixed complete-reference control requires all source frames')

            def frames(points):
                return [{'t_ms': timestamp, 'lm': lm}
                        for timestamp, lm in zip(timestamps, points.tolist(), strict=True)]

            reference = adapted(frames(raw), spec)
            base = source['base']

            def evaluate(trial):
                return diagnostics(evaluator, base, reference, trial, spec)

            positive = evaluate(frames(raw))
            controls = generate_attacks(raw)
            phase = np.linspace(0, 1, len(raw))
            shifted_phase = phase + 0.10 * np.sin(np.pi * phase)
            shifted = np.stack([np.interp(shifted_phase, phase, point)
                                for point in raw.reshape(len(raw), 42).T], axis=1)
            warped = evaluate(frames(shifted.reshape(raw.shape)))
            trials = {'exact_replay': positive, 'forward_time_warp': warped}
            for name in CONDITIONS:
                if name not in trials:
                    trials[name] = evaluate(frames(controls[name]))
                rows[name].append((positive, warped, trials[name]))
            missing = frames(raw)
            missing[len(missing) // 2]['lm'] = None
            rows['middle_frame_missing'].append((positive, warped, evaluate(missing)))
            for other_key, other in evaluator.sources.items():
                if other_key != key:
                    other_raw = [f['lm'] for f in other['raw_frames'] if f['lm'] is not None]
                    trial = evaluate(frames(resample(other_raw, len(raw))))
                    rows['wrong_library'].append((positive, warped, trial))

    return {
        'scope': 'published_coordinates_known_sources_only',
        'sources': len(rows['exact_replay']),
        'python': platform.python_version(),
        'numpy': np.__version__,
        'node': subprocess.check_output(['node', '--version'], text=True).strip(),
        'handcaptcha_commit': subprocess.check_output(
            ['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
        'dtw_radius': 'round(0.1 * frame_count)',
        'time_axis': 'published nominal frame timestamps',
        'forward_time_warp': 'phase + 0.10 * sin(pi * phase), linear interpolation',
        'comparison': 'candidate error minus exact replay error on the same target',
        'conditions': summarize(rows),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new output path')
    report = compare(args.source_root.resolve())
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
