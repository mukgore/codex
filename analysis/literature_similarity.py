"""Compare hand sequence descriptors and exercise cutoff selection on public fixtures."""
import argparse
import json
from pathlib import Path
import subprocess

from dtw import __version__ as dtw_version, dtw
import numpy as np

from g4_lab.actual import ActualEvaluator
from g4_lab.attacks import generate_attacks
from g4_lab.run import resample
from validation_v03.adapters import InputSpec, normalize_frame
from validation_v03.standard_metrics import constrained_dtw, select_validation_threshold


PHASE_SAMPLES = 32
RADIUS = 3
TIPS = [4, 8, 12, 16, 20]
PARENTS = [0, 1, 2, 3, 0, 5, 6, 7, 0, 9, 10, 11, 0, 13, 14, 15, 0, 17, 18, 19]
FUSION = ('angle_dtw', 'palm_bone_dtw', 'angle_ddtw')
CONTROL_NAMES = ('hold_first', 'hold_middle', 'hold_last', 'endpoint_interpolation', 'reverse')


def derivative(values):
    """Keogh–Pazzani local slope, with nearest interior estimate at the edges."""
    inside = ((values[1:-1] - values[:-2]) + (values[2:] - values[:-2]) / 2) / 2
    return np.concatenate((inside[:1], inside, inside[-1:]))


def describe(points, spec):
    xy, angles = map(np.asarray, zip(*(normalize_frame(frame, spec) for frame in points)))
    phase_xy = resample(xy, PHASE_SAMPLES)
    bones = phase_xy[:, 1:] - phase_xy[:, PARENTS]
    bones /= np.linalg.norm(bones, axis=2, keepdims=True)
    palm_x = phase_xy[:, 9]
    palm_x = palm_x / np.linalg.norm(palm_x, axis=1, keepdims=True)
    palm_y = np.column_stack((-palm_x[:, 1], palm_x[:, 0]))
    bone_local = np.stack(((bones * palm_x[:, None]).sum(axis=2),
                           (bones * palm_y[:, None]).sum(axis=2)), axis=2)
    phase = np.linspace(0, 1, len(angles))
    grid = np.linspace(0, 1, PHASE_SAMPLES)
    angle_grid = np.stack([np.interp(grid, phase, feature) for feature in angles.T], axis=1)
    return {'angle_dtw': angle_grid, 'palm_bone_dtw': bone_local.reshape(PHASE_SAMPLES, -1),
            'angle_ddtw': derivative(angle_grid),
            'tips': xy[:, TIPS]}


def distances(reference, response):
    result = {name: -constrained_dtw(reference[name], response[name], radius=RADIUS).path_rmse
              for name in FUSION}
    # Match each fingertip separately. The submitted response is the query.
    tip_pairs = list(zip(response['tips'].transpose(1, 0, 2),
                         reference['tips'].transpose(1, 0, 2), strict=True))
    for name, options in (
        ('tip_open_dtw', dict(step_pattern='asymmetric', open_begin=True, open_end=True)),
        ('tip_closed_dtw', dict(step_pattern='asymmetric')),
    ):
        result[name] = -float(np.mean([
            dtw(trial, target, **options).normalizedDistance for trial, target in tip_pairs
        ]))
    return result


def warped(points, spec, warp, rotation):
    phase = np.linspace(0, 1, len(points))
    shifted = phase + warp * np.sin(np.pi * phase)
    interpolated = np.stack([np.interp(shifted, phase, p)
                             for p in points.reshape(len(points), -1).T], axis=1)
    xy = interpolated.reshape(points.shape)
    aspect = np.array([spec.width, spec.height])
    wrist = xy[:, :1, :]
    cosine, sine = np.cos(np.deg2rad(rotation)), np.sin(np.deg2rad(rotation))
    matrix = np.array([[cosine, -sine], [sine, cosine]])
    return (((xy - wrist) * aspect) @ matrix.T) / aspect + wrist


def trials(root):
    with ActualEvaluator(root) as evaluator:
        keys = sorted(evaluator.sources)
        if keys != [f'custom{index:02}' for index in range(1, 9)]:
            raise ValueError('Study requires the fixed eight-clip public pool')
        raw = {key: np.asarray([frame['lm'] for frame in source['raw_frames']], dtype=float)
               for key, source in evaluator.sources.items()}
        for key in keys:
            source = evaluator.sources[key]
            clip = evaluator.clips[key]
            info = json.loads((root / clip['landmarks_file']).read_text(encoding='utf-8'))['video_info']
            fps = info['fps']
            spec = InputSpec(info['width'], info['height'], 'normalized_xy', 'ms', False, 2 / fps)
            points = raw[key]
            reference = describe(points, spec)
            controls = generate_attacks(points)
            inputs = [(name, False, key, controls[name]) for name in CONTROL_NAMES]
            inputs.append(('middle_half_only', False, key, points[len(points)//4:len(points)//4 + len(points)//2 + 1]))
            inputs.extend(('wrong_library', False, donor, resample(raw[donor], len(points)))
                          for donor in keys if donor != key)
            inputs.extend(('synthetic_match', True, key, warped(points, spec, warp, rotation))
                          for warp, rotation in ((-.10, 0), (.10, 0), (-.10, -10), (.10, 10)))
            inputs.append(('exact_replay', None, key, points))
            for name, positive, donor, sequence in inputs:
                frames = [{'t_ms': i * 1000 / fps, 'lm': lm}
                          for i, lm in enumerate(sequence.tolist())]
                legacy = evaluator.evaluate(key, frames)
                yield {
                    'target': key, 'donor': donor, 'condition': name, 'positive': positive,
                    'gate': legacy['gate_pass'], 'legacy_pass': legacy['score_pass'],
                    'scores': {'legacy': legacy['score']['captcha'],
                               **distances(reference, describe(sequence, spec))},
                }


def counts(rows, accepted):
    result = {}
    for row, accept in zip(rows, accepted, strict=True):
        group = result.setdefault(row['condition'], {'accepted': 0, 'n': 0})
        group['accepted'] += int(accept)
        group['n'] += 1
    return result


def fold(calibration, test):
    labels = [int(row['positive']) for row in calibration]
    test_labels = np.array([row['positive'] for row in test], dtype=bool)
    calibration_matrix = np.array([[row['scores'][name] for name in FUSION] for row in calibration])
    q25, center, q75 = np.quantile(calibration_matrix, [0.25, 0.50, 0.75], axis=0)
    iqr = q75 - q25
    if np.any(iqr <= 0):
        raise ValueError('Cannot scale a feature with zero calibration IQR')

    def scores(rows, method):
        if method == 'fusion':
            matrix = np.array([[row['scores'][name] for name in FUSION] for row in rows])
            return ((matrix - center) / iqr).mean(axis=1)
        return np.array([row['scores'][method] for row in rows])

    result = {}
    for name in (*calibration[0]['scores'], 'fusion'):
        train_scores = scores(calibration, name)
        point = select_validation_threshold(labels, train_scores, split_name='validation',
                                            min_human_accept=1, max_attack_accept=1)
        perfect = select_validation_threshold(labels, train_scores, split_name='validation',
                                              min_human_accept=1, max_attack_accept=0)
        test_scores = scores(test, name)
        accepted = test_scores >= point['threshold']
        differences = test_scores[test_labels, None] - test_scores[~test_labels][None, :]
        result[name] = {
            'threshold': point['threshold'],
            'zero_negative_accept_feasible_on_calibration': perfect is not None,
            'calibration': counts(calibration, train_scores >= point['threshold']),
            'test': counts(test, accepted),
            'test_auc': float(np.mean((differences > 0) + 0.5 * (differences == 0))),
        }
    return {'fusion_calibration_median': center.tolist(), 'fusion_calibration_iqr': iqr.tolist(),
            'methods': result}


def evaluate(root):
    rows = list(trials(root))
    sets = ({'custom01', 'custom03', 'custom05', 'custom08'},
            {'custom02', 'custom04', 'custom06', 'custom07'})

    def subset(keys):
        return [row for row in rows if row['positive'] is not None
                and {row['target'], row['donor']} <= keys]

    folds = [fold(subset(calibration), subset(test))
             for calibration, test in (sets, sets[::-1])]
    return {
        'scope': 'known_public_2d_fixtures_synthetic_matches_no_human_labels',
        'source_revision': subprocess.check_output(
            ['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
        'numpy': np.__version__, 'dtw_python': dtw_version,
        'phase_samples': PHASE_SAMPLES, 'dtw_radius': RADIUS,
        'clip_splits': [sorted(keys) for keys in sets],
        'historical_score_gate_full_pool': counts(
            rows, [row['legacy_pass'] and row['gate'] for row in rows]),
        'historical_score_full_pool': counts(rows, [row['legacy_pass'] for row in rows]),
        'oracle_replay_raw_errors_max': {
            name: max(-row['scores'][name] for row in rows if row['condition'] == 'exact_replay')
            for name in (*FUSION, 'tip_open_dtw', 'tip_closed_dtw')},
        'folds': folds,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new output path')
    report = evaluate(args.source_root.resolve())
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
