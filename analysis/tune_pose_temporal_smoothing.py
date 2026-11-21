"""Compare a small, predeclared set of temporal smoothers on validation clips only."""

import argparse
import json
from pathlib import Path

import numpy as np

from occluded_pose_benchmark import (
    JOINTS, evaluate, features, read_recorded, read_synthetic, smooth_temporal,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--synthetic', type=Path, required=True)
    parser.add_argument('--recorded', type=Path, required=True)
    parser.add_argument('--weights-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--domains', nargs='+', choices=('2d', '3d', 'recorded'),
                        default=('2d', '3d', 'recorded'))
    args = parser.parse_args()
    source_report = json.loads(args.report.read_text(encoding='utf8'))
    clips = [*read_synthetic(args.synthetic), *read_recorded(args.recorded)]
    result = {'selection': 'minimum validation NME; no test clips scored', 'domains': {}}
    for mode in args.domains:
        summary = source_report['domains'][mode]['selected']
        path = args.weights_dir / (mode + '.npz')
        with np.load(path, allow_pickle=False) as data:
            weights, offset = data['weights'], data['offset']
            kind = str(data['feature_kind'].item())
        validation = [clip for clip in clips if clip['mode'] == mode and clip['split'] == 'validation']
        raw = {clip['name']: (features(clip['rgb'], kind) @ weights + offset).reshape(-1, len(JOINTS), 2)
               for clip in validation}
        trials = []
        for sigma in (0., .35, .5, .75, 1., 1.5, 2.):
            predictions = {name: smooth_temporal(points, sigma) for name, points in raw.items()}
            rows = []
            for clip in validation:
                xy = clip['xy']
                valid = np.isfinite(xy).all(axis=(1, 2))
                aspect = np.array([512. / 420, 1.]) if mode != 'recorded' else np.ones(2)
                delta = np.linalg.norm((predictions[clip['name']][valid] - xy[valid]) * aspect, axis=2)
                palm = np.linalg.norm((xy[valid, 9] - xy[valid, 0]) * aspect, axis=1)
                normalized = delta / palm[:, None]
                hidden = None if clip['hidden'] is None else normalized[clip['hidden'][valid]]
                rows.append({'nme': float(normalized.mean()),
                             'pck_20': float((normalized <= .2).mean()),
                             'hidden_nme': None if hidden is None or not len(hidden) else float(hidden.mean())})
            trial = {'sigma': sigma,
                     'nme': float(np.mean([row['nme'] for row in rows])),
                     'pck_20': float(np.mean([row['pck_20'] for row in rows])),
                     'hidden_nme': (float(np.mean([row['hidden_nme'] for row in rows if row['hidden_nme'] is not None]))
                                    if mode != 'recorded' else None)}
            trials.append(trial)
        best = min(trials, key=lambda row: row['nme'])
        result['domains'][mode] = {'base_model': summary['model'], 'validation_trials': trials,
                                   'selected_sigma': best['sigma'], 'selected_validation': best}
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf8')
    print(json.dumps({mode: row['selected_validation'] for mode, row in result['domains'].items()}))


if __name__ == '__main__':
    main()
