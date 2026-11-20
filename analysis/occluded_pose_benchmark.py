"""Offline image-to-joint pilot with source-group splits and coordinate metrics."""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

JOINTS = (
    'WRIST', 'THUMB_CMC', 'THUMB_MCP', 'THUMB_IP', 'THUMB_TIP', 'INDEX_MCP', 'INDEX_PIP',
    'INDEX_DIP', 'INDEX_TIP', 'MIDDLE_MCP', 'MIDDLE_PIP', 'MIDDLE_DIP', 'MIDDLE_TIP',
    'RING_MCP', 'RING_PIP', 'RING_DIP', 'RING_TIP', 'PINKY_MCP', 'PINKY_PIP',
    'PINKY_DIP', 'PINKY_TIP',
)
# Keep both challenge clips generated from one PRNG seed in the same split.
# The generator emits two clips per seed, so splitting by gesture family alone
# lets correlated scene/motion draws cross the train/validation/test boundary.
SYNTHETIC_SEED_SPLIT = {
    **{seed: 'train' for seed in range(1, 17)},
    **{seed: 'validation' for seed in range(17, 21)},
    **{seed: 'test' for seed in range(21, 25)},
}
RECORDED_SPLIT = {
    'custom01': 'train', 'custom02': 'train', 'custom06': 'train',
    'custom04': 'train', 'custom05': 'train',
    'custom07': 'validation', 'custom03': 'test', 'custom08': 'test',
}
CV_SIZE = (20, 20)
PENALTIES = (.01, .1, 1., 10.)
MODELS = ('rgb_ridge', 'temporal_edges_ridge')


def read_synthetic(root):
    manifest = json.loads((root / 'annotations.json').read_text(encoding='utf8'))
    for clip in manifest['clips']:
        frames = clip['frames']
        rgb = np.fromfile(root / (clip['name'] + '.rgb'), dtype=np.uint8).reshape(
            len(frames), manifest['height'], manifest['width'], 3)
        yield {
            'name': clip['name'], 'source': clip['source'], 'mode': clip['mode'],
            'split': SYNTHETIC_SEED_SPLIT[int(clip['source'].split('-')[1])], 'rgb': rgb,
            'xy': np.asarray([f['xy'] for f in frames], dtype=np.float32),
            'hidden': np.asarray([f['hidden'] for f in frames], dtype=bool),
        }


def read_recorded(root):
    manifest = json.loads((root / 'pool_manifest.json').read_text(encoding='utf8'))
    for clip in manifest['clips']:
        data = json.loads((root / clip['landmarks_file']).read_text(encoding='utf-8-sig'))
        info = data['video_info']
        frames = data['frames']
        capture = cv2.VideoCapture(str(root / clip['video_file']))
        images, points = [], []
        try:
            for index, reference in enumerate(frames):
                ok, image = capture.read()
                if not ok or reference['frame_idx'] != index:
                    raise ValueError(f'Video/reference frame mismatch in {clip["clip_id"]}')
                if index % 4:
                    continue
                images.append(cv2.cvtColor(cv2.resize(image, (80, 66), interpolation=cv2.INTER_AREA),
                                           cv2.COLOR_BGR2RGB))
                if reference['detected']:
                    lm = reference['landmarks_px']
                    points.append([[lm[name]['x'] / info['width'], lm[name]['y'] / info['height']]
                                   for name in JOINTS])
                else:
                    points.append(np.full((21, 2), np.nan))
            if capture.read()[0]:
                raise ValueError(f'Extra video frames in {clip["clip_id"]}')
        finally:
            capture.release()
        yield {
            'name': clip['clip_id'], 'source': clip['clip_id'], 'mode': 'recorded',
            'handedness': clip['handedness'],
            'split': RECORDED_SPLIT[clip['clip_id']], 'rgb': np.asarray(images),
            'xy': np.asarray(points, dtype=np.float32), 'hidden': None,
        }


def features(rgb, kind):
    """Feature extraction receives pixels only, including within-clip context."""
    small = np.stack([cv2.resize(image, CV_SIZE, interpolation=cv2.INTER_AREA)
                      for image in rgb]).astype(np.float32) / 255
    color = small.reshape(len(small), -1)
    if kind == 'rgb_ridge':
        return color
    grey = small.mean(axis=3)
    gradients = [np.stack([cv2.Sobel(image, cv2.CV_32F, dx, dy, ksize=3)
                           for image in grey]).reshape(len(grey), -1) / 4
                 for dx, dy in ((1, 0), (0, 1))]
    prev = np.concatenate([grey[:1], grey[:-1]])
    following = np.concatenate([grey[1:], grey[-1:]])
    motion = [(grey - prev).reshape(len(grey), -1), (following - grey).reshape(len(grey), -1)]
    return np.concatenate([color, *gradients, *motion], axis=1)


def fit_ridge(x, y, penalty):
    center = x.mean(axis=0)
    average = y.mean(axis=0)
    x = x - center
    y = y - average
    kernel = x @ x.T
    kernel.flat[::len(kernel) + 1] += penalty
    weights = x.T @ np.linalg.solve(kernel, y)
    return weights, average - center @ weights


def evaluate(clips, predict, feature_kind, *, extract=features):
    rows = []
    for clip in clips:
        xy = clip['xy']
        valid = np.isfinite(xy).all(axis=(1, 2))
        if not valid.any():
            continue
        prediction = predict(extract(clip['rgb'], feature_kind)).reshape(-1, len(JOINTS), 2)
        # Isotropic scale using the original canvas aspect ratio and reference palm length.
        aspect = np.array([512. / 420, 1.]) if clip['mode'] != 'recorded' else np.ones(2)
        delta = np.linalg.norm((prediction[valid] - xy[valid]) * aspect, axis=2)
        palm = np.linalg.norm((xy[valid, 9] - xy[valid, 0]) * aspect, axis=1)
        if not np.isfinite(delta).all() or not np.all(palm > 0):
            raise ValueError(f'Invalid predictions or palm reference in {clip["name"]}')
        norm = delta / palm[:, None]
        hidden = None if clip['hidden'] is None else norm[clip['hidden'][valid]]
        rows.append({
            'frames': len(xy), 'reference_frames': int(valid.sum()),
            'nme': float(norm.mean()), 'pck_20': float((norm <= .2).mean()),
            'hidden_nme': float(hidden.mean()) if hidden is not None and len(hidden) else None,
        })
    return {
        'clips': len(clips), 'scored_clips': len(rows),
        'frames': sum(len(clip['xy']) for clip in clips), 'reference_frames': sum(r['reference_frames'] for r in rows),
        **{key: float(np.mean([r[key] for r in rows if r[key] is not None]))
           if any(r[key] is not None for r in rows) else None for key in ('nme', 'pck_20', 'hidden_nme')},
    }


def run_domain(clips, weights_path=None):
    partitions = {name: [clip for clip in clips if clip['split'] == name]
                  for name in ('train', 'validation', 'test')}
    source_sets = [{clip['source'] for clip in part} for part in partitions.values()]
    if any(not sources for sources in source_sets) or any(
            left & right for i, left in enumerate(source_sets) for right in source_sets[i + 1:]):
        raise ValueError('Expected three nonempty and source-disjoint partitions')
    training = partitions['train']
    train_y = np.concatenate([clip['xy'] for clip in training]).reshape(-1, 42)
    valid = np.isfinite(train_y).all(axis=1)
    configs = []
    for kind in MODELS:
        train_x = np.concatenate([features(clip['rgb'], kind) for clip in training])
        for penalty in PENALTIES:
            weights, offset = fit_ridge(train_x[valid], train_y[valid], penalty)
            predict = lambda inputs: inputs @ weights + offset
            result = evaluate(partitions['validation'], predict, kind)
            configs.append((result, kind, penalty, weights, offset))
    winner, kind, penalty, weights, offset = min(configs, key=lambda item: item[0]['nme'])
    if weights_path is not None:
        with weights_path.open('xb') as handle:
            np.savez_compressed(handle, weights=weights, offset=offset, feature_kind=kind)
    return {
        'partition_clips': {key: len(value) for key, value in partitions.items()},
        'selected': {'model': kind, 'penalty': penalty, 'validation': winner},
        'validation_trials': [{'model': model, 'penalty': reg, **result} for result, model, reg, *_ in configs],
        'held_out': evaluate(partitions['test'], lambda inputs: inputs @ weights + offset, kind),
        'hamer': {'state': 'not_measured_on_this_pilot'},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--synthetic', type=Path, required=True)
    parser.add_argument('--recorded', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--weights-dir', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if args.weights_dir is not None:
        args.weights_dir.mkdir()
    clips = [*read_synthetic(args.synthetic), *read_recorded(args.recorded)]
    report = {
        'scope': 'offline_xy_landmark_estimation_pilot',
        'metrics': 'clip-macro palm-normalized image-plane distance (NME) and PCK@0.2',
        'recorded_reference': 'existing tracker annotations, not independent anatomical ground truth',
        'synthetic_split': {'seed_groups': {'train': '1-16', 'validation': '17-20', 'test': '21-24'},
                            'group_key': 'generator PRNG seed; both clips kept together'},
        'recorded_split': RECORDED_SPLIT,
        'domains': {mode: run_domain([clip for clip in clips if clip['mode'] == mode],
                                     None if args.weights_dir is None else args.weights_dir / (mode + '.npz'))
                    for mode in ('2d', '3d', 'recorded')},
    }
    with args.output.open('x', encoding='utf8') as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps({mode: {'selected': row['selected']['model'], **row['held_out']}
                      for mode, row in report['domains'].items()}))


if __name__ == '__main__':
    main()
