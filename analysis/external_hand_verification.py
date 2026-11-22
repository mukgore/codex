"""Independent external-video evaluation for grouped-v15 and hand pose baselines.

Run this file once per backend in the corresponding pinned Python runtime, then
run --backend aggregate. External videos and model predictions stay outside Git.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from occluded_pose_benchmark import features, smooth_temporal  # noqa: E402
from hand_pose_metrics import (  # noqa: E402
    mean_per_joint_acceleration_error, pck_curve_and_auc,
    vera_prediction_stability,
)

W, H, MASK_X, MASK_Y, MASK_R = 512, 420, 256, 210, 95
JOINTS = 21
JOINT_NAMES = (
    'WRIST', 'THUMB_CMC', 'THUMB_MCP', 'THUMB_IP', 'THUMB_TIP', 'INDEX_MCP',
    'INDEX_PIP', 'INDEX_DIP', 'INDEX_TIP', 'MIDDLE_MCP', 'MIDDLE_PIP',
    'MIDDLE_DIP', 'MIDDLE_TIP', 'RING_MCP', 'RING_PIP', 'RING_DIP',
    'RING_TIP', 'PINKY_MCP', 'PINKY_PIP', 'PINKY_DIP', 'PINKY_TIP',
)
ANGLE_TRIPLES = (
    (0, 5, 6), (5, 6, 7), (6, 7, 8), (0, 9, 10), (9, 10, 11),
    (10, 11, 12), (0, 13, 14), (13, 14, 15), (14, 15, 16),
    (0, 17, 18), (17, 18, 19), (18, 19, 20), (0, 1, 2),
    (1, 2, 3), (2, 3, 4),
)
PROD_WEIGHTS = {'dtw_angle': .38, 'accel': .37, 'angle': .25}
PROD_MAX = {'angle': 46.9413, 'dtw_angle': 44.0014, 'accel': .1926}
PROD_THRESHOLD = .25
BONES = ((0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
         (0, 9), (9, 10), (10, 11), (11, 12), (0, 13), (13, 14), (14, 15),
         (15, 16), (0, 17), (17, 18), (18, 19), (19, 20))

# One fixed RGB sequence per official GigaHands demo activity, selected before
# inference by palm-center coverage of the original center disk (same fixed mask).
SEQUENCES = (
    ('p36-tea-0010', 'right', 'brics-odroid-016_cam0_1727030430697566'),
    ('p41-boxing-0021', 'left', 'brics-odroid-026_cam1_1726962101793664'),
    ('p41-plant-0004', 'left', 'brics-odroid-023_cam0_1726963265350610'),
    ('p44-dog-0004', 'right', 'brics-odroid-015_cam1_1725202053204578'),
    ('p52-instrument-0034', 'right', 'brics-odroid-024_cam0_1726248075919808'),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def process_memory_high_water():
    """Read Windows process RSS/pagefile high-water marks at process exit."""
    if sys.platform != 'win32':
        return {'state': 'not_available', 'reason': 'Windows memory API is unavailable'}

    class Counters(ctypes.Structure):
        _fields_ = [
            ('cb', ctypes.wintypes.DWORD), ('PageFaultCount', ctypes.wintypes.DWORD),
            ('PeakWorkingSetSize', ctypes.c_size_t), ('WorkingSetSize', ctypes.c_size_t),
            ('QuotaPeakPagedPoolUsage', ctypes.c_size_t), ('QuotaPagedPoolUsage', ctypes.c_size_t),
            ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t), ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
            ('PagefileUsage', ctypes.c_size_t), ('PeakPagefileUsage', ctypes.c_size_t),
            ('PrivateUsage', ctypes.c_size_t),
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel32, psapi = ctypes.windll.kernel32, ctypes.windll.psapi
    kernel32.GetCurrentProcess.restype = ctypes.wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [
        ctypes.wintypes.HANDLE, ctypes.POINTER(Counters), ctypes.wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = ctypes.wintypes.BOOL
    ok = psapi.GetProcessMemoryInfo(
        kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
    if not ok:
        return {'state': 'not_available', 'winerror': ctypes.GetLastError()}
    return {
        'state': 'measured', 'measurement': 'Windows PROCESS_MEMORY_COUNTERS_EX at process exit',
        'peak_working_set_bytes': int(counters.PeakWorkingSetSize),
        'working_set_at_exit_bytes': int(counters.WorkingSetSize),
        'peak_pagefile_bytes': int(counters.PeakPagefileUsage),
        'private_bytes_at_exit': int(counters.PrivateUsage),
    }


def json_array(value: np.ndarray):
    """Serialize arrays with null for missing labels/detections."""
    arr = np.asarray(value)
    obj = arr.astype(object)
    obj[~np.isfinite(arr)] = None
    return obj.tolist()


def read_clip(data_root: Path, session: str, side: str, stem: str):
    session_root = data_root / session
    videos = list((session_root / 'rgb_vid').rglob(stem + '.mp4'))
    labels = list((session_root / 'keypoints_2d' / side).rglob(stem + '.jsonl'))
    if len(videos) != 1 or len(labels) != 1:
        raise FileNotFoundError(f'{session}/{stem}: videos={len(videos)} labels={len(labels)}')
    label_path, video_path = labels[0], videos[0]
    rows = [np.asarray(json.loads(line), dtype=np.float32).reshape(JOINTS, 3)
            for line in label_path.read_text(encoding='utf8').splitlines() if line.strip()]
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise OSError(f'cannot open {video_path}')
    source_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    source_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    expected_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    scale = min(W / source_w, H / source_h)
    resized_w, resized_h = round(source_w * scale), round(source_h * scale)
    offset_x, offset_y = (W - resized_w) // 2, (H - resized_h) // 2
    images, transform_seconds = [], 0.
    yy, xx = np.mgrid[0:H, 0:W]
    blend = (xx / max(1, W - 1) + yy / max(1, H - 1)) / 2
    c0 = np.array([36, 54, 73], dtype=np.float32)
    c1 = np.array([17, 27, 38], dtype=np.float32)
    background = (c0[None, None, :] * (1 - blend[..., None]) +
                  c1[None, None, :] * blend[..., None]).astype(np.uint8)
    read_start = time.perf_counter()
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        t0 = time.perf_counter()
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        small = cv2.resize(rgb, (resized_w, resized_h), interpolation=cv2.INTER_AREA)
        # The source canvas background is a muted diagonal gradient; use its
        # matching corner color in contain-bars and retain the source aspect.
        canvas = background.copy()
        canvas[offset_y:offset_y + resized_h, offset_x:offset_x + resized_w] = small
        images.append(canvas)
        transform_seconds += time.perf_counter() - t0
    cap.release()
    decode_seconds = time.perf_counter() - read_start
    if len(images) != len(rows) or len(images) != expected_frames:
        raise ValueError(f'{stem}: decoded={len(images)} labels={len(rows)} metadata={expected_frames}')
    xy = np.stack([r[:, :2] for r in rows])
    visibility = np.stack([r[:, 2] for r in rows]) > 0
    # Apply the same contain transform to annotations as to frames.
    xy[..., 0] = (xy[..., 0] * scale + offset_x) / W
    xy[..., 1] = (xy[..., 1] * scale + offset_y) / H
    xy[~visibility] = np.nan
    hand = np.asarray(images, dtype=np.uint8)
    circle = ((np.arange(W)[None, :] - MASK_X) ** 2 +
              (np.arange(H)[:, None] - MASK_Y) ** 2 <= MASK_R ** 2)
    masked = hand.copy()
    masked[:, circle] = np.array([7, 11, 16], dtype=np.uint8)
    pixel_xy = xy * np.array([W, H], dtype=np.float32)
    hidden = np.linalg.norm(pixel_xy - np.array([MASK_X, MASK_Y]), axis=2) <= MASK_R
    hidden &= np.isfinite(xy).all(axis=2)
    return {
        'session': session, 'side': side, 'stem': stem, 'video_path': video_path,
        'label_path': label_path, 'video_sha256': sha256(video_path),
        'label_sha256': sha256(label_path), 'source_width': source_w,
        'source_height': source_h, 'fps': fps, 'frames': len(images),
        'duration_seconds': len(images) / fps if fps else None,
        'rgb': hand, 'masked_rgb': masked, 'xy': xy, 'hidden': hidden,
        'visibility': visibility, 'decode_seconds': decode_seconds,
        'transform_seconds': transform_seconds,
        'mask': {'canvas_width': W, 'canvas_height': H, 'center_x': MASK_X,
                 'center_y': MASK_Y, 'radius_px': MASK_R, 'rgb': [7, 11, 16]},
        'letterbox': {'scale': scale, 'offset_x': offset_x, 'offset_y': offset_y,
                      'width': resized_w, 'height': resized_h},
    }


def load_local_predictors(weights_dir: Path):
    result = {}
    for name in ('2d', '3d'):
        with np.load(weights_dir / (name + '.npz'), allow_pickle=False) as archive:
            artifact = dict(archive)
        result[name] = artifact
    return result


def local_predict(rgb: np.ndarray, artifact: dict):
    kind = str(artifact['feature_kind'].item())
    t0 = time.perf_counter()
    x = features(rgb, kind)
    feature_seconds = time.perf_counter() - t0
    t1 = time.perf_counter()
    points = x @ artifact['weights'] + artifact['offset']
    sigma = float(artifact.get('temporal_sigma', 0.))
    points = smooth_temporal(points.reshape(-1, JOINTS, 2), sigma).reshape(-1, JOINTS, 2)
    prediction_seconds = time.perf_counter() - t1
    return points.astype(np.float32), feature_seconds, prediction_seconds


def run_backend(backend: str, data_root: Path, weights_dir: Path,
                hamer_source: Path | None, hamer_checkpoint: Path | None,
                output_dir: Path, realtime_models: Path | None = None):
    output_dir.mkdir(parents=True, exist_ok=True)
    torch = None
    if backend in ('local', 'hamer'):
        if backend == 'hamer':
            if not hamer_source or not hamer_checkpoint:
                raise ValueError('HaMeR requires --hamer-source and --hamer-checkpoint')
            sys.path.insert(0, str(hamer_source.resolve(strict=True)))
            from measure_hamer_pose import make_estimator
            torch = __import__('torch')
            torch.set_num_threads(4)
            init_start = time.perf_counter()
            predictor = make_estimator(hamer_source.resolve(strict=True), hamer_checkpoint.resolve(strict=True))
            init_seconds = time.perf_counter() - init_start
        else:
            init_start = time.perf_counter()
            predictors = load_local_predictors(weights_dir)
            init_seconds = time.perf_counter() - init_start
    elif backend == 'realtime':
        if not realtime_models:
            raise ValueError('realtime requires --realtime-models')
        from train_realtime_occluded_hand_models import StreamingEstimator
        init_start = time.perf_counter()
        torch = __import__('torch')
        torch.set_num_threads(4)
        predictors = {}
        artifact_info = {}
        for name in ('2d_A_current', '2d_B_past_current',
                     '3d_A_current', '3d_B_past_current'):
            estimator, artifact = StreamingEstimator.from_checkpoint(
                realtime_models / f'{name}.pt')
            predictors[name] = estimator
            artifact_info[name] = {
                'mode': artifact['mode'], 'domain': artifact['domain'],
                'input_size_wh': artifact['input_size_wh'],
                'checkpoint_sha256': sha256(realtime_models / f'{name}.pt'),
            }
        init_seconds = time.perf_counter() - init_start
    elif backend == 'mediapipe':
        import mediapipe as mp
        init_seconds = 0.
        predictors = None
    else:
        raise ValueError(backend)

    output = {'backend': backend, 'setup_seconds': init_seconds, 'records': []}
    if backend == 'local':
        output['environment'] = {'python': sys.version, 'opencv': cv2.__version__,
                                 'numpy': np.__version__, 'inference_stack': 'NumPy/OpenCV ridge regression',
                                 'device': 'CPU',
                                 'weights': {name: sha256(weights_dir / (name + '.npz'))
                                             for name in ('2d', '3d')}}
    elif backend == 'hamer':
        output['environment'] = {'python': sys.version, 'opencv': cv2.__version__,
                                 'numpy': np.__version__, 'torch': torch.__version__,
                                 'device': 'CPU', 'threads': torch.get_num_threads(),
                                 'upstream_revision': '3a01849f4148352e9260b69bf28b65d1671a4905',
                                 'checkpoint_sha256': sha256(hamer_checkpoint)}
    elif backend == 'realtime':
        output['environment'] = {'python': sys.version, 'opencv': cv2.__version__,
                                 'numpy': np.__version__, 'torch': torch.__version__,
                                 'device': 'CPU', 'threads': torch.get_num_threads(),
                                 'inference': 'frame-by-frame A/B; resize included in per-frame timing',
                                 'models': artifact_info}
    else:
        output['environment'] = {'python': sys.version, 'opencv': cv2.__version__,
                                 'numpy': np.__version__, 'mediapipe': mp.__version__,
                                 'device': 'CPU', 'graph': 'mediapipe.solutions.hands.Hands'}
    for session, side, stem in SEQUENCES:
        clip = read_clip(data_root, session, side, stem)
        variants = {'unoccluded': clip['rgb'], 'circle': clip['masked_rgb']}
        clip_record = {k: v for k, v in clip.items()
                       if k not in ('rgb', 'masked_rgb', 'xy', 'hidden', 'visibility', 'video_path', 'label_path')}
        clip_record['xy'] = json_array(clip['xy'])
        clip_record['hidden'] = clip['hidden'].tolist()
        clip_record['models'] = {}
        for condition, rgb in variants.items():
            gt = clip['xy']
            condition_output = {}
            if backend == 'local':
                for name, artifact in predictors.items():
                    pred, feat_s, infer_s = local_predict(rgb, artifact)
                    condition_output[name] = {
                        'xy': json_array(pred), 'detection': np.ones(len(pred), dtype=bool).tolist(),
                        'feature_seconds': feat_s, 'inference_seconds': infer_s,
                        'total_seconds': feat_s + infer_s,
                        'feature_kind': str(artifact['feature_kind'].item()),
                        'temporal_sigma': float(artifact.get('temporal_sigma', 0.)),
                    }
            elif backend == 'realtime':
                for name, estimator in predictors.items():
                    estimator.reset()
                    warm_start = time.perf_counter()
                    estimator.predict(rgb[0])
                    warmup_seconds = time.perf_counter() - warm_start
                    estimator.reset()
                    predictions, frame_times = [], []
                    for image in rgb:
                        t0 = time.perf_counter()
                        predictions.append(estimator.predict(image))
                        frame_times.append(time.perf_counter() - t0)
                    pred = np.asarray(predictions, dtype=np.float32)
                    condition_output[name] = {
                        'xy': json_array(pred),
                        'detection': np.ones(len(pred), dtype=bool).tolist(),
                        'total_seconds': float(sum(frame_times)),
                        'frame_seconds': frame_times,
                        'warmup_seconds': warmup_seconds,
                        'input_size_wh': list(estimator.input_size),
                        'state_reset_per_video_and_condition': True,
                        'future_frames_accessed': False,
                    }
            elif backend == 'hamer':
                right = side == 'right'
                warm_start = time.perf_counter()
                warm = predictor(rgb[:min(2, len(rgb))], right, 'recorded')
                warmup_seconds = time.perf_counter() - warm_start
                del warm
                frame_chunks, chunk_times = [], []
                for start in range(0, len(rgb), 8):
                    t0 = time.perf_counter()
                    chunk = predictor(rgb[start:start + 8], right, 'recorded')
                    chunk_times.append(time.perf_counter() - t0)
                    frame_chunks.append(chunk.reshape(-1, JOINTS, 2))
                pred = np.concatenate(frame_chunks).astype(np.float32)
                condition_output['hamer'] = {
                    'xy': json_array(pred), 'detection': np.ones(len(pred), dtype=bool).tolist(),
                    'total_seconds': float(sum(chunk_times)), 'chunk_seconds': chunk_times,
                    'chunk_size': 8, 'warmup_frames_excluded': min(2, len(rgb)),
                    'warmup_seconds': warmup_seconds,
                    'handedness_given': side,
                }
            else:
                model_start = time.perf_counter()
                hands = mp.solutions.hands.Hands(
                    static_image_mode=False, max_num_hands=2, model_complexity=1,
                    min_detection_confidence=.5, min_tracking_confidence=.5)
                model_init_seconds = time.perf_counter() - model_start
                try:
                    # Warm up graph state using one image outside recorded timings.
                    warm_start = time.perf_counter()
                    hands.process(rgb[0])
                    warmup_seconds = time.perf_counter() - warm_start
                    pred = np.full((len(rgb), JOINTS, 2), np.nan, dtype=np.float32)
                    detected = np.zeros(len(rgb), dtype=bool)
                    frame_times = []
                    for i, image in enumerate(rgb):
                        t0 = time.perf_counter()
                        result = hands.process(image)
                        frame_times.append(time.perf_counter() - t0)
                        candidates = result.multi_hand_landmarks or []
                        if not candidates:
                            continue
                        wrist = gt[i, 0]
                        options = [np.asarray([[p.x, p.y] for p in hand.landmark], dtype=np.float32)
                                   for hand in candidates]
                        selected = min(options, key=lambda points: float(np.linalg.norm(points[0] - wrist)))
                        pred[i] = selected
                        detected[i] = True
                finally:
                    hands.close()
                condition_output['mediapipe'] = {
                    'xy': json_array(pred), 'detection': detected.tolist(),
                    'total_seconds': float(sum(frame_times)), 'frame_seconds': frame_times,
                    'initialization_seconds': model_init_seconds, 'warmup_seconds': warmup_seconds,
                    'handedness_given': False, 'candidate_matching': 'nearest wrist to GT after inference',
                    'static_image_mode': False, 'max_num_hands': 2,
                    'model_complexity': 1, 'min_detection_confidence': .5,
                    'min_tracking_confidence': .5,
                }
            clip_record['models'][condition] = condition_output
        output['records'].append(clip_record)
        print(json.dumps({'backend': backend, 'video': stem, 'frames': clip['frames']}, ensure_ascii=False), flush=True)
    output['environment']['process_memory'] = process_memory_high_water()
    target = output_dir / f'{backend}_predictions.json'
    with target.open('x', encoding='utf8') as stream:
        json.dump(output, stream, allow_nan=False, separators=(',', ':'))
        stream.write('\n')
    print(json.dumps({'backend': backend, 'output': str(target), 'setup_seconds': init_seconds}, ensure_ascii=False))


def angle_trace(points, p, j, d):
    v1, v2 = points[:, p] - points[:, j], points[:, d] - points[:, j]
    den = np.maximum(np.linalg.norm(v1, axis=1) * np.linalg.norm(v2, axis=1), 1e-8)
    dot = np.sum(v1 * v2, axis=1)
    return np.degrees(np.arccos(np.clip(dot / den, -1, 1)))


def normalized_pose(trace):
    result = trace - trace[:, :1, :]
    palm = np.maximum(np.linalg.norm(result[:, 9, :], axis=1), 1e-6)
    return result / palm[:, None, None]


def resample(trace, n):
    if len(trace) == n:
        return trace
    old = np.linspace(0, 1, len(trace))
    new = np.linspace(0, 1, n)
    return np.stack([np.interp(new, old, trace[:, j, d])
                     for j in range(JOINTS) for d in range(2)], axis=1).reshape(n, JOINTS, 2)


def production_errors(target, observed):
    target = normalized_pose(target)
    observed = normalized_pose(observed)
    aligned = resample(target, len(observed))
    angle_error = np.mean([np.mean(np.abs(angle_trace(observed, p, j, d) -
                                             angle_trace(aligned, p, j, d)))
                           for p, j, d in ANGLE_TRIPLES])
    # Exact hand_captcha_prod.html windowed offset-tolerant comparator: resize
    # target to round(1.2 * observed frames), then test every equal-length window.
    stretched = resample(target, round(len(observed) * 1.2))
    dtw_error = min(np.mean([np.mean(np.abs(angle_trace(observed, p, j, d) -
                                              angle_trace(window, p, j, d)))
                             for p, j, d in ANGLE_TRIPLES])
                    for start in range(len(stretched) - len(observed) + 1)
                    for window in (stretched[start:start + len(observed)],))
    observed_accel = np.linalg.norm(np.diff(observed, n=2, axis=0)[:, 1:, :], axis=2).mean(axis=1)
    target_accel = np.linalg.norm(np.diff(aligned, n=2, axis=0)[:, 1:, :], axis=2).mean(axis=1)
    accel_error = float(np.mean(np.abs(observed_accel - target_accel)))
    return {'angle': float(angle_error), 'dtw_angle': float(dtw_error), 'accel': accel_error}


def metrics(target, hidden, prediction, detection, fps):
    point_valid = np.isfinite(target).all(axis=2)
    coordinate_ok = np.isfinite(prediction).all(axis=(1, 2))
    detected = np.asarray(detection, dtype=bool) & coordinate_ok
    frame_valid = point_valid.any(axis=1)
    palm_px = np.linalg.norm((target[:, 9] - target[:, 0]) * np.array([W, H]), axis=1)
    point_valid &= palm_px[:, None] > 0
    pred_px = prediction * np.array([W, H])
    target_px = target * np.array([W, H])
    point_error_px = np.full((len(target), JOINTS), np.nan)
    available = point_valid & detected[:, None]
    point_error_px[available] = np.linalg.norm(pred_px[available] - target_px[available], axis=1)
    norm_error = point_error_px / np.maximum(palm_px[:, None], 1e-8)
    ref_count = int(point_valid.sum())
    det_count = int((point_valid & detected[:, None]).sum())
    good20 = np.isfinite(norm_error) & (norm_error <= .2)
    hidden = np.asarray(hidden, dtype=bool) & point_valid
    visible = point_valid & ~hidden
    pck_auc = pck_curve_and_auc(norm_error, point_valid)
    acceleration_error = mean_per_joint_acceleration_error(
        target, prediction, detected, fps, pixel_scale=(W, H), palm_px=palm_px)
    prediction_valid_joint = np.isfinite(prediction).all(axis=-1)
    temporal_stability = vera_prediction_stability(
        prediction, prediction_valid_joint, detected)

    def mean_or_none(values):
        values = np.asarray(values)
        values = values[np.isfinite(values)]
        return float(values.mean()) if len(values) else None

    def group_summary(mask):
        errors_px = point_error_px[mask]
        errors_norm = norm_error[mask]
        return {'joint_frames': int(mask.sum()),
                'matched_joint_frames': int(np.isfinite(errors_norm).sum()),
                'mean_position_error_px': mean_or_none(errors_px),
                'mean_position_error_palm_normalized': mean_or_none(errors_norm),
                'pck20': float(np.sum(np.isfinite(errors_norm) & (errors_norm <= .2)) / max(1, mask.sum())),
                'pck_curve_and_auc': pck_curve_and_auc(norm_error, mask)}

    finger_groups = {
        'wrist': (0,), 'thumb': (1, 2, 3, 4), 'index': (5, 6, 7, 8),
        'middle': (9, 10, 11, 12), 'ring': (13, 14, 15, 16),
        'little': (17, 18, 19, 20),
    }
    joint_type_groups = {
        'CMC': (1,), 'MCP': (2, 5, 9, 13, 17), 'PIP': (6, 10, 14, 18),
        'IP': (3,), 'DIP': (7, 11, 15, 19), 'TIP': (4, 8, 12, 16, 20),
    }
    def subset_mask(ids):
        result = np.zeros_like(point_valid)
        result[:, ids] = point_valid[:, ids]
        return result

    by_finger = {name: group_summary(subset_mask(ids)) for name, ids in finger_groups.items()}
    by_joint_type = {name: group_summary(subset_mask(ids)) for name, ids in joint_type_groups.items()}

    edge_px, edge_norm = [], []
    for a, b in BONES:
        edge_ok = point_valid[:, a] & point_valid[:, b] & detected
        if edge_ok.any():
            pred_len = np.linalg.norm(pred_px[:, a] - pred_px[:, b], axis=1)
            true_len = np.linalg.norm(target_px[:, a] - target_px[:, b], axis=1)
            delta = np.abs(pred_len[edge_ok] - true_len[edge_ok])
            edge_px.extend(delta.tolist())
            edge_norm.extend((delta / np.maximum(palm_px[edge_ok], 1e-8)).tolist())
    angle_errors = []
    for p, j, d in ANGLE_TRIPLES:
        angle_ok = point_valid[:, p] & point_valid[:, j] & point_valid[:, d] & detected
        if angle_ok.any():
            true_angles = np.degrees(np.arccos(np.clip(
                np.sum((target_px[:, p] - target_px[:, j]) * (target_px[:, d] - target_px[:, j]), axis=1) /
                np.maximum(np.linalg.norm(target_px[:, p] - target_px[:, j], axis=1) *
                           np.linalg.norm(target_px[:, d] - target_px[:, j], axis=1), 1e-8), -1, 1)))
            pred_angles = np.degrees(np.arccos(np.clip(
                np.sum((pred_px[:, p] - pred_px[:, j]) * (pred_px[:, d] - pred_px[:, j]), axis=1) /
                np.maximum(np.linalg.norm(pred_px[:, p] - pred_px[:, j], axis=1) *
                           np.linalg.norm(pred_px[:, d] - pred_px[:, j], axis=1), 1e-8), -1, 1)))
            angle_errors.extend(np.abs(pred_angles[angle_ok] - true_angles[angle_ok]).tolist())

    hidden_fraction = hidden.sum(axis=1) / np.maximum(point_valid.sum(axis=1), 1)
    level_bins = [('none', 0., 0.), ('0-25%', 0., .25), ('25-50%', .25, .5),
                  ('50-75%', .5, .75), ('75-100%', .75, 1.01)]
    by_occlusion_level = {}
    for name, low, high in level_bins:
        if name == 'none':
            frame_mask = frame_valid & (hidden_fraction == 0)
        else:
            frame_mask = frame_valid & (hidden_fraction > low if low == 0 else hidden_fraction >= low) & (hidden_fraction < high)
        hidden_point_mask = point_valid & frame_mask[:, None] & hidden
        all_point_mask = point_valid & frame_mask[:, None]
        by_occlusion_level[name] = {
            'frames': int(frame_mask.sum()), 'mean_hidden_joint_fraction': mean_or_none(hidden_fraction[frame_mask]),
            'hidden_joint_frames': int(hidden_point_mask.sum()),
            'hidden_joint_error_px_valid_predictions': mean_or_none(point_error_px[hidden_point_mask]),
            'hidden_joint_error_palm_normalized_valid_predictions': mean_or_none(norm_error[hidden_point_mask]),
            'hidden_joint_pck_curve_and_auc': pck_curve_and_auc(norm_error, hidden_point_mask),
            'all_joint_frames': int(all_point_mask.sum()),
            'all_joint_error_px_valid_predictions': mean_or_none(point_error_px[all_point_mask]),
            'all_joint_error_palm_normalized_valid_predictions': mean_or_none(norm_error[all_point_mask]),
            'all_joint_pck_curve_and_auc': pck_curve_and_auc(norm_error, all_point_mask),
            'detection_rate': float(np.mean(detected[frame_mask])) if frame_mask.any() else None,
        }

    # Mark each hidden joint-frame with its contiguous hidden-run duration.
    run_lengths = np.zeros_like(hidden, dtype=np.int32)
    for joint in range(JOINTS):
        row = hidden[:, joint]
        starts = np.flatnonzero(row & np.r_[True, ~row[:-1]])
        ends = np.flatnonzero(row & np.r_[~row[1:], True]) + 1
        for start, end in zip(starts, ends):
            run_lengths[start:end, joint] = end - start
    run_bins = [('<0.1s', 0., .1), ('0.1-0.5s', .1, .5), ('0.5-1s', .5, 1.), ('>=1s', 1., math.inf)]
    by_occlusion_duration = {}
    for name, low, high in run_bins:
        dur = run_lengths / max(fps, 1e-8)
        duration_members = hidden & (dur >= low) & (dur < high)
        point_mask = duration_members & detected[:, None]
        by_occlusion_duration[name] = {
            'hidden_joint_frames': int(duration_members.sum()),
            'mean_position_error_px': mean_or_none(point_error_px[point_mask]),
            'mean_position_error_palm_normalized': mean_or_none(norm_error[point_mask]),
        }
    missed = ref_count - det_count
    return {
        'frames': len(target), 'reference_joint_frames': ref_count,
        'detected_joint_frames': det_count,
        'reference_frames_with_any_label': int(frame_valid.sum()),
        'detected_frames': int((detected & frame_valid).sum()),
        'detection_success_rate': float((detected & frame_valid).sum() / max(1, frame_valid.sum())),
        'detection_failure_rate': float(1 - (detected & frame_valid).sum() / max(1, frame_valid.sum())),
        'invalid_prediction_frames': int((~detected & frame_valid).sum()),
        'frames_with_out_of_bounds_prediction_rate': float(np.mean(
            ((prediction < 0) | (prediction > 1)).any(axis=2)[detected])) if detected.any() else None,
        'mean_position_error_px_valid_frames': mean_or_none(point_error_px[available]),
        'mean_position_error_palm_normalized_valid_frames': mean_or_none(norm_error[available]),
        'coverage_adjusted_error_px_missed_as_one_palm': float(
            np.nansum(point_error_px) / max(1, ref_count) + missed / max(1, ref_count) * np.mean(palm_px[frame_valid])),
        'pck20_all_reference_joints': float(np.sum(good20) / max(1, ref_count)),
        'pck_curve_and_auc': pck_auc,
        'by_finger': by_finger,
        'by_joint_type': by_joint_type,
        'mean_per_joint_acceleration_error': acceleration_error,
        'prediction_temporal_stability': temporal_stability,
        'occluded_joints': group_summary(hidden), 'visible_joints': group_summary(visible),
        'mean_bone_length_error_px': mean_or_none(edge_px),
        'mean_bone_length_error_palm_normalized': mean_or_none(edge_norm),
        'mean_absolute_2d_joint_angle_error_degrees_15triples': mean_or_none(angle_errors),
        'mean_occluded_joint_fraction_per_frame': mean_or_none(hidden_fraction[frame_valid]),
        'by_occlusion_level': by_occlusion_level,
        'by_occlusion_duration': by_occlusion_duration,
        'mask_boundary_rule': 'hidden iff annotated point-center distance to (256,210) is <=95 px; boundary included',
    }


def paired_video_bootstrap(video_rows, left, right, metric, *, replicates=10000, seed=20261122):
    pairs = []
    for row in video_rows:
        a, b = row['results'].get(left), row['results'].get(right)
        if a is None or b is None:
            continue
        av, bv = a.get(metric), b.get(metric)
        if av is not None and bv is not None and np.isfinite(av) and np.isfinite(bv):
            pairs.append(float(av) - float(bv))
    if not pairs:
        return None
    values = np.asarray(pairs, dtype=np.float64)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(replicates, len(values)))
    draws = values[indices].mean(axis=1)
    return {'paired_videos': len(values), 'left_minus_right_mean': float(values.mean()),
            'ci95_video_bootstrap': [float(np.quantile(draws, .025)),
                                     float(np.quantile(draws, .975))],
            'bootstrap_unit': 'video; resamples video-level paired differences, not frames',
            'replicates': replicates, 'seed': seed}


def aggregate(output_dir: Path):
    backends = {}
    for name in ('local', 'realtime', 'hamer', 'mediapipe'):
        path = output_dir / f'{name}_predictions.json'
        backends[name] = json.loads(path.read_text(encoding='utf8'))
    records = {}
    for backend, data in backends.items():
        for clip in data['records']:
            key = clip['stem']
            records.setdefault(key, {'clip': clip, 'results': {}})
            for condition, models in clip['models'].items():
                for model, result in models.items():
                    pred = np.asarray(result['xy'], dtype=np.float32)
                    det = np.asarray(result['detection'], dtype=bool)
                    gt = np.asarray(clip['xy'], dtype=np.float32)
                    hidden = np.asarray(clip['hidden'], dtype=bool)
                    mm = metrics(gt, hidden, pred, det, float(clip['fps']))
                    valid = np.isfinite(gt).all(axis=(1, 2)) & det & np.isfinite(pred).all(axis=(1, 2))
                    prod = production_errors(gt[valid], pred[valid]) if valid.sum() >= 5 else None
                    if prod:
                        dr = mm['detection_success_rate']
                        estimated = {k: float(np.clip(dr * (1 - prod[k] / PROD_MAX[k]), 0, 1))
                                     for k in ('angle', 'dtw_angle', 'accel')}
                        score = (estimated['dtw_angle'] * PROD_WEIGHTS['dtw_angle'] +
                                 estimated['accel'] * PROD_WEIGHTS['accel'] +
                                 estimated['angle'] * PROD_WEIGHTS['angle'])
                        prod = {'raw_error': prod, 'estimated_component_scores': estimated,
                                'challenge_score_analog': float(score),
                                'challenge_threshold': PROD_THRESHOLD,
                                'pass_on_threshold_analog': bool(score >= PROD_THRESHOLD)}
                    records[key]['results'][f'{backend}:{model}:{condition}'] = {
                        **mm, 'production_score_analog': prod,
                        'runtime': {k: v for k, v in result.items()
                                    if k not in ('xy', 'detection')},
                    }
    video_rows = []
    for key, bundle in records.items():
        clip = bundle['clip']
        video_rows.append({
            'session': clip['session'], 'selected_side': clip['side'], 'video': clip['stem'],
            'video_sha256': clip['video_sha256'], 'label_sha256': clip['label_sha256'],
            'source_resolution': [clip['source_width'], clip['source_height']],
            'fps': clip['fps'], 'frames': clip['frames'],
            'duration_seconds': clip['duration_seconds'],
            'mask': clip['mask'], 'letterbox': clip['letterbox'],
            'decode_seconds': clip['decode_seconds'], 'transform_seconds': clip['transform_seconds'],
            'results': bundle['results'],
        })
    model_keys = sorted({k for r in video_rows for k in r['results']})
    summary = {}
    for model in model_keys:
        vals = [r['results'][model]['runtime']['total_seconds'] for r in video_rows]
        per_frame = [t / r['frames'] for t, r in zip(vals, video_rows)]
        summary[model] = {
            'videos': len(vals), 'total_model_seconds': float(sum(vals)),
            'mean_video_seconds': float(statistics.mean(vals)),
            'median_video_seconds': float(statistics.median(vals)),
            'min_video_seconds': float(min(vals)), 'max_video_seconds': float(max(vals)),
            'mean_ms_per_frame': float(statistics.mean(per_frame) * 1000),
            'median_ms_per_frame': float(statistics.median(per_frame) * 1000),
            'p95_ms_per_frame_across_video_averages': float(np.percentile(per_frame, 95) * 1000),
            'per_video_latency': [
                {'video': r['video'], 'seconds': float(r['results'][model]['runtime']['total_seconds']),
                 'ms_per_frame': float(r['results'][model]['runtime']['total_seconds'] / r['frames'] * 1000),
                 'ratio_to_model_mean_video_seconds': float(r['results'][model]['runtime']['total_seconds'] /
                                                            statistics.mean(vals)),
                 'at_least_1_5x_mean': bool(r['results'][model]['runtime']['total_seconds'] >=
                                            1.5 * statistics.mean(vals))}
                for r in video_rows],
        }
    accuracy_summary = {}
    for model in model_keys:
        rows = [r['results'][model] for r in video_rows]

        def pool(field, count_field):
            numerator = sum((row.get(field) or 0) * row.get(count_field, 0)
                            for row in rows if row.get(field) is not None)
            denominator = sum(row.get(count_field, 0) for row in rows
                              if row.get(field) is not None)
            return float(numerator / denominator) if denominator else None

        def pool_group(group_name, field):
            numerator = sum((row[group_name].get(field) or 0) * row[group_name].get('matched_joint_frames', 0)
                            for row in rows if row[group_name].get(field) is not None)
            denominator = sum(row[group_name].get('matched_joint_frames', 0)
                              for row in rows if row[group_name].get(field) is not None)
            return float(numerator / denominator) if denominator else None

        auc_num = sum((row['pck_curve_and_auc'].get('auc') or 0) *
                      row['pck_curve_and_auc'].get('eligible_joint_frames', 0)
                      for row in rows if row['pck_curve_and_auc'].get('auc') is not None)
        auc_den = sum(row['pck_curve_and_auc'].get('eligible_joint_frames', 0)
                      for row in rows if row['pck_curve_and_auc'].get('auc') is not None)
        accel_weight = sum(row['mean_per_joint_acceleration_error'].get('pixel_per_s2', 0) *
                           row['mean_per_joint_acceleration_error'].get('valid_joint_windows', 0)
                           for row in rows if row['mean_per_joint_acceleration_error'].get('pixel_per_s2') is not None)
        accel_den = sum(row['mean_per_joint_acceleration_error'].get('valid_joint_windows', 0)
                        for row in rows if row['mean_per_joint_acceleration_error'].get('pixel_per_s2') is not None)
        accuracy_summary[model] = {
            'aggregation': 'joint-frame micro averages pooled across the same five clips; per-video and video-macro values remain in videos[]',
            'mpjpe_2d_px_valid_predictions_micro': pool('mean_position_error_px_valid_frames', 'detected_joint_frames'),
            'mpjpe_2d_palm_normalized_valid_predictions_micro': pool('mean_position_error_palm_normalized_valid_frames', 'detected_joint_frames'),
            'pck20_all_labeled_joint_frames_micro': pool('pck20_all_reference_joints', 'reference_joint_frames'),
            'pck_auc_0_to_0_5_palm_micro': float(auc_num / auc_den) if auc_den else None,
            'occluded_mpjpe_2d_px_valid_predictions_micro': pool_group('occluded_joints', 'mean_position_error_px'),
            'occluded_mpjpe_2d_palm_normalized_valid_predictions_micro': pool_group('occluded_joints', 'mean_position_error_palm_normalized'),
            'visible_mpjpe_2d_px_valid_predictions_micro': pool_group('visible_joints', 'mean_position_error_px'),
            'visible_mpjpe_2d_palm_normalized_valid_predictions_micro': pool_group('visible_joints', 'mean_position_error_palm_normalized'),
            'detection_success_rate_micro': pool('detection_success_rate', 'reference_frames_with_any_label'),
            'mean_per_joint_acceleration_error_px_per_s2_micro': float(accel_weight / accel_den) if accel_den else None,
            'jacc_median_video_x100': float(np.median([r['prediction_temporal_stability']['jacc_image_relative']
                                                       for r in rows if r['prediction_temporal_stability']['jacc_image_relative'] is not None]) * 100)
            if any(r['prediction_temporal_stability']['jacc_image_relative'] is not None for r in rows) else None,
            'jjerk_median_video_x100': float(np.median([r['prediction_temporal_stability']['jjerk_image_relative']
                                                        for r in rows if r['prediction_temporal_stability']['jjerk_image_relative'] is not None]) * 100)
            if any(r['prediction_temporal_stability']['jjerk_image_relative'] is not None for r in rows) else None,
            'ev_median_video_x100': float(np.median([r['prediction_temporal_stability']['ev_image_relative']
                                                     for r in rows if r['prediction_temporal_stability']['ev_image_relative'] is not None]) * 100)
            if any(r['prediction_temporal_stability']['ev_image_relative'] is not None for r in rows) else None,
        }
    paired = {}
    metrics_to_compare = ('mean_position_error_px_valid_frames',
                          'mean_position_error_palm_normalized_valid_frames',
                          'pck20_all_reference_joints', 'detection_success_rate')
    for i, left in enumerate(model_keys):
        for right in model_keys[i + 1:]:
            if left.rsplit(':', 1)[-1] != right.rsplit(':', 1)[-1]:
                continue
            pair = {}
            for metric_name in metrics_to_compare:
                result = paired_video_bootstrap(video_rows, left, right, metric_name)
                if result is not None:
                    pair[metric_name] = result
            if pair:
                paired[f'{left}__minus__{right}'] = pair
    report = {
        'scope': 'external real-video transfer check; existing offline estimator plus separately trained A/B estimators',
        'dataset': 'GigaHands five official demo sequences; CC BY-NC 4.0; markerless capture-derived annotations',
        'selection': 'one camera per each of five demo sessions, chosen before inference to maximize the share of annotated palm centers within the fixed center disk; this is a mask-focused convenience sample, not a random benchmark split',
        'mask': {'canonical_canvas': [W, H], 'center_xy_px': [MASK_X, MASK_Y],
                 'radius_px': MASK_R, 'fill_rgb': [7, 11, 16], 'applied_to_every_frame': True},
        'reference': 'GigaHands per-frame 2D keypoint JSONL; transformed with the same aspect-preserving contain geometry; labels with confidence <= 0 omitted',
        'metrics': {'primary_position': '2D MPJPE (mean per-joint Euclidean distance), pixel and palm-normalized; conditional on finite detected predictions',
                    'pck': 'PCK@0.02, 0.05, 0.10, 0.20, 0.30, 0.50 palm lengths; misses count incorrect over all labeled joints',
                    'pck_auc': 'normalized trapezoidal area under PCK on [0, 0.50] palm lengths; not the CrossFuNet 20-50 mm 3D interval',
                    'temporal_accuracy': 'GT-relative mean per-joint acceleration error, second finite difference times fps^2; px/s^2 and palm-length/s^2; complete detected GT triplets only',
                    'temporal_stability': 'VERA-Hand release-code Jacc/Jjerk/Ev on prediction-only image-relative coordinates, kept separate from GT accuracy',
                    'other_custom_summaries': '20 bone-length absolute differences; 15-triple 2D angle absolute error in degrees; by-finger and by-joint-type subsets',
                    'occlusion_strata': 'hidden/visible joints, mask-coverage levels, and contiguous occlusion duration bins; these are subgroups of base metrics',
                    'missed_predictions': 'excluded from valid-output MPJPE/acceleration but retained as failures in PCK and in separately reported detection failure'},
        'metric_audit_document': 'docs/reproducibility/hand_pose_metric_audit.md',
        'prod_score_comparison': {'source': 'usability/handcaptcha/hand_captcha_prod.html',
                                  'method': 'exact landmark angle triples, wrist/palm-normalized trajectory, 1.2x target resample and sliding offset window for the component named DTW, second differences for accel, detection-rate scaling, MX and W2 thresholds/weights',
                                  'scope_note': 'computed as a whole-clip model-vs-GigaHands-reference analog; not an actual CAPTCHA session, participant result, or pass-rate claim'},
        'timing': {'device': 'CPU only; model initialization/warm-up and shared video decode/transform reported separately',
                   'summary': summary},
        'accuracy_summary': accuracy_summary,
        'paired_video_comparisons': {'scope': 'same selected videos and same occlusion condition; each metric reports left minus right',
                                     'results': paired,
                                     'limitation': 'five selected clips provide very low bootstrap resolution and include two clips from participant p41; intervals are descriptive, not population-level evidence'},
        'videos': video_rows,
    }
    target = output_dir / 'external_hand_verification.json'
    with target.open('x', encoding='utf8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'output': str(target), 'videos': len(video_rows), 'models': summary}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=('local', 'realtime', 'hamer', 'mediapipe', 'aggregate'), required=True)
    parser.add_argument('--data-root', type=Path)
    parser.add_argument('--weights-dir', type=Path)
    parser.add_argument('--hamer-source', type=Path)
    parser.add_argument('--hamer-checkpoint', type=Path)
    parser.add_argument('--realtime-models', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.backend == 'aggregate':
        aggregate(args.output_dir)
    else:
        if not args.data_root or not args.weights_dir:
            raise ValueError('data-root and weights-dir are required')
        run_backend(args.backend, args.data_root, args.weights_dir,
                    args.hamer_source, args.hamer_checkpoint, args.output_dir,
                    args.realtime_models)


if __name__ == '__main__':
    main()
