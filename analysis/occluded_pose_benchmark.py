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
    **{seed: 'train' for seed in range(1, 25)},
    **{seed: 'train' for seed in range(77, 101)},
    **{seed: 'validation' for seed in range(101, 113)},
    **{seed: 'validation' for seed in range(125, 137)},
    **{seed: 'test' for seed in range(113, 125)},
    **{seed: 'test' for seed in range(137, 149)},
    **{seed: 'test' for seed in range(149, 161)},
    **{seed: 'validation' for seed in range(161, 173)},
    **{seed: 'test' for seed in range(173, 185)},
    **{seed: 'train' for seed in range(185, 197)},
    **{seed: 'test' for seed in range(197, 209)},
    **{seed: 'test' for seed in range(209, 221)},
    **{seed: 'train' for seed in range(221, 233)},
    **{seed: 'test' for seed in range(233, 245)},
    **{seed: 'train' for seed in range(245, 257)},
    **{seed: 'test' for seed in range(257, 269)},
    **{seed: 'train' for seed in range(269, 281)},
    **{seed: 'test' for seed in range(281, 293)},
    **{seed: 'train' for seed in range(293, 305)},
    **{seed: 'test' for seed in range(305, 317)},
}
RECORDED_SPLIT = {
    'custom01': 'train', 'custom02': 'train', 'custom06': 'train',
    'custom04': 'train', 'custom05': 'train',
    'custom07': 'validation', 'custom03': 'test', 'custom08': 'test',
}
CV_SIZES = {'72': (72, 72), '80': (80, 80)}
PENALTIES = (.0001, .001, .01, .1, 1., 10.)
TEMPORAL_SIGMAS = (0., .35, .5, .75, 1., 1.5, 2.)
MODELS = tuple(f'{kind}_{size}' for size in CV_SIZES
               for kind in ('temporal_color_edges_ridge',))


def seed_ranges(split):
    seeds = sorted(seed for seed, name in SYNTHETIC_SEED_SPLIT.items() if name == split)
    ranges = []
    for seed in seeds:
        if not ranges or seed > ranges[-1][1] + 1:
            ranges.append([seed, seed])
        else:
            ranges[-1][1] = seed
    return [str(start) if start == end else f'{start}-{end}' for start, end in ranges]


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
                target_height = round(80 * info['height'] / info['width'])
                images.append(cv2.cvtColor(cv2.resize(image, (80, target_height), interpolation=cv2.INTER_AREA),
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
    base_kind, size = kind.rsplit('_', 1)
    small = np.stack([cv2.resize(image, CV_SIZES[size], interpolation=cv2.INTER_AREA)
                      for image in rgb]).astype(np.float32) / 255
    color = small.reshape(len(small), -1)
    if base_kind == 'rgb_ridge':
        return color
    if base_kind == 'temporal_color_edges_ridge':
        channel_edges = [np.stack([
            np.stack([cv2.Sobel(image[..., channel], cv2.CV_32F, dx, dy, ksize=3)
                      for channel in range(3)], axis=-1)
            for image in small]).reshape(len(small), -1) / 4
            for dx, dy in ((1, 0), (0, 1))]
        prev_color = np.concatenate([small[:1], small[:-1]])
        next_color = np.concatenate([small[1:], small[-1:]])
        color_motion = [(small - prev_color).reshape(len(small), -1),
                        (next_color - small).reshape(len(small), -1)]
        return np.concatenate([color, *channel_edges, *color_motion], axis=1)
    grey = small.mean(axis=3)
    gradients = [np.stack([cv2.Sobel(image, cv2.CV_32F, dx, dy, ksize=3)
                           for image in grey]).reshape(len(grey), -1) / 4
                 for dx, dy in ((1, 0), (0, 1))]
    prev = np.concatenate([grey[:1], grey[:-1]])
    following = np.concatenate([grey[1:], grey[-1:]])
    motion = [(grey - prev).reshape(len(grey), -1), (following - grey).reshape(len(grey), -1)]
    return np.concatenate([color, *gradients, *motion], axis=1)


def smooth_temporal(points, sigma):
    """Apply a symmetric Gaussian filter along time to frame-wise joint predictions."""
    if sigma <= 0 or len(points) < 3:
        return points
    radius = max(1, int(np.ceil(3 * sigma)))
    offsets = np.arange(-radius, radius + 1, dtype=np.float32)
    kernel = np.exp(-.5 * (offsets / sigma) ** 2)
    kernel /= kernel.sum()
    flat = points.reshape(len(points), -1)
    padded = np.pad(flat, ((radius, radius), (0, 0)), mode='edge')
    filtered = np.stack([np.convolve(padded[:, column], kernel, mode='valid')
                         for column in range(flat.shape[1])], axis=1)
    return filtered.reshape(points.shape).astype(points.dtype, copy=False)


def fit_ridge(x, y, penalty):
    center = x.mean(axis=0)
    average = y.mean(axis=0)
    x = x - center
    y = y - average
    kernel = x @ x.T
    kernel.flat[::len(kernel) + 1] += penalty
    weights = x.T @ np.linalg.solve(kernel, y)
    return weights, average - center @ weights


def fit_ridge_grid(x, y, penalties):
    """Solve a regularization grid from one shared kernel eigendecomposition."""
    center = x.mean(axis=0)
    average = y.mean(axis=0)
    centered_x = x - center
    centered_y = y - average
    kernel = centered_x @ centered_x.T
    eigenvalues, eigenvectors = np.linalg.eigh(kernel)
    projected_y = eigenvectors.T @ centered_y
    fitted = []
    for penalty in penalties:
        dual = eigenvectors @ (projected_y / (eigenvalues[:, None] + penalty))
        weights = centered_x.T @ dual
        fitted.append((weights, average - center @ weights))
    return fitted


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
            'name': clip['name'], 'source': clip['source'],
            'frames': len(xy), 'reference_frames': int(valid.sum()),
            'nme': float(norm.mean()), 'pck_20': float((norm <= .2).mean()),
            'hidden_nme': float(hidden.mean()) if hidden is not None and len(hidden) else None,
        })
    return {
        'clips': len(clips), 'scored_clips': len(rows),
        'frames': sum(len(clip['xy']) for clip in clips), 'reference_frames': sum(r['reference_frames'] for r in rows),
        'per_clip': rows,
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
        for penalty, (weights, offset) in zip(PENALTIES, fit_ridge_grid(train_x[valid], train_y[valid], PENALTIES)):
            for sigma in TEMPORAL_SIGMAS:
                def predict(inputs, weights=weights, offset=offset, sigma=sigma):
                    xy = (inputs @ weights + offset).reshape(-1, len(JOINTS), 2)
                    return smooth_temporal(xy, sigma).reshape(-1, 42)
                result = evaluate(partitions['validation'], predict, kind)
                configs.append((result, kind, penalty, sigma, weights, offset))
    winner, kind, penalty, sigma, weights, offset = min(configs, key=lambda item: item[0]['nme'])
    if weights_path is not None:
        with weights_path.open('xb') as handle:
            np.savez_compressed(handle, weights=weights, offset=offset, feature_kind=kind,
                                temporal_sigma=sigma)
    return {
        'partition_clips': {key: len(value) for key, value in partitions.items()},
        'selected': {'model': kind, 'penalty': penalty, 'temporal_sigma': sigma, 'validation': winner},
        'validation_trials': [{'model': model, 'penalty': reg, 'temporal_sigma': smooth, **result}
                              for result, model, reg, smooth, *_ in configs],
        'held_out': evaluate(partitions['test'],
                             lambda inputs: smooth_temporal((inputs @ weights + offset).reshape(-1, 21, 2), sigma).reshape(-1, 42),
                             kind),
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
        'synthetic_split': {'seed_groups': {name: seed_ranges(name)
                                            for name in ('train', 'validation', 'test')},
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
