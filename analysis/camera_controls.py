"""Offline camera-input controls using existing handcaptcha videos and MediaPipe.

No camera, browser, network, participant capture or protection endpoint is used.
Only aggregate diagnostics are written. The existing pool is development material.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
from zipfile import ZipFile

import numpy as np

from g4_lab.actual import ActualEvaluator
from validation_v03.adapters import InputSpec, adapt_segment, compare_contiguous_blocks


def read_video(path, info):
    import cv2

    cap = cv2.VideoCapture(str(path))
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not cap.isOpened() or not math.isclose(fps, info['fps'], rel_tol=0.001):
            raise ValueError('Video could not be opened or FPS differs from the reference')
        frames = []
        while (item := cap.read())[0]:
            frame = item[1]
            if frame.shape[:2] != (info['height'], info['width']):
                raise ValueError('Video size differs from the reference')
            if len(frames) >= len(info['frames']):
                raise ValueError('Decoded more frames than the reference')
            frames.append(frame)
    finally:
        cap.release()
    if len(frames) < 3 or len(frames) != len(info['frames']):
        raise ValueError('Decoded frame count differs from the reference')
    return frames


def render_masked(frames, records, level):
    import cv2

    if len(frames) != len(records):
        raise ValueError('Mask record count differs from video')
    masked = []
    for index, (frame, record) in enumerate(zip(frames, records, strict=True)):
        if record['frame_idx'] != index or not record['detected']:
            raise ValueError('Unaligned or missing archive mask')
        mask = record['occlusion_levels'][level]
        center = tuple(mask['mask_center'][axis] for axis in ('x', 'y'))
        radius = mask['mask_radius']
        if (any(type(value) is not int for value in (*center, radius))
                or not (0 <= center[0] < frame.shape[1] and 0 <= center[1] < frame.shape[0])
                or radius <= 0):
            raise ValueError('Invalid archive circle')
        masked.append(cv2.circle(frame.copy(), center, radius, (0, 0, 0), -1))
    return masked


def track(frames, fps):
    import cv2
    import mediapipe as mp

    # A fresh state for each trial. Repeated-image input goes through video tracking,
    # so temporal jitter remains observable rather than forcing landmarks constant.
    with mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=1,
                                  model_complexity=1, min_detection_confidence=0.5,
                                  min_tracking_confidence=0.5) as hands:
        for index, frame in enumerate(frames):
            result = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            landmarks = result.multi_hand_landmarks
            yield {'t_ms': index * 1000 / fps,
                   'lm': [[float(p.x), float(p.y)] for p in landmarks[0].landmark]
                   if landmarks else None}


def adapted(frames, spec):
    return adapt_segment([{'t': f['t_ms'], 'lm': f['lm']} for f in frames], spec)


def angular_activity(blocks):
    """Mean absolute angle displacement per observed second within valid blocks."""
    total_degrees = total_seconds = 0.0
    for block in blocks:
        angles = np.asarray(block['angles_degrees'])
        total_degrees += float(np.abs(np.diff(angles, axis=0)).mean(axis=1).sum())
        total_seconds += block['times_seconds'][-1] - block['times_seconds'][0]
    return total_degrees / total_seconds if total_seconds else None


def diagnostics(evaluator, base, reference, frames, spec):
    detected = sum(frame['lm'] is not None for frame in frames)
    trial = adapted(frames, spec)
    result = evaluator.call({'op': 'evaluate', 'base': base, 'frames': frames})
    features = None
    if (reference['analyzed_frames'] == trial['analyzed_frames'] == len(frames)
            and len(reference['blocks']) == len(trial['blocks']) == 1):
        compared = compare_contiguous_blocks(
            reference['blocks'][0], trial['blocks'][0],
            dtw_radius=round(len(frames) * 0.1), max_gap_seconds=spec.max_gap_seconds)
        features = {name: compared[name] for name in (
            'angle_phase_grid_mae_degrees', 'dtw_angle_path_rmse',
            'acceleration_phase_aligned_mae_hand_lengths_per_second_squared')}
    return {'attempted_frames': len(frames), 'detected_frames': detected,
            'valid_contiguous_frames': trial['analyzed_frames'],
            'angular_activity_degrees_per_second': angular_activity(trial['blocks']),
            'legacy_score': result['score']['captcha'], 'legacy_score_pass': result['score_pass'],
            'offline_gate_pass': result['gate_pass'],
            'complete_trial_candidate_features': features}


def trial_pair(evaluator, frames, base, raw_reference, info, *, archive_controls=False):
    fps = info['fps']
    spec = InputSpec(info['width'], info['height'], 'normalized_xy', 'ms', False, 2 / fps)
    reference = adapted(raw_reference, spec)
    conditions = {'moving_video': frames, 'repeated_middle_image': [frames[len(frames)//2]] * len(frames)}
    if archive_controls:
        conditions.update(repeated_first_image=[frames[0]] * len(frames),
                          repeated_last_image=[frames[-1]] * len(frames),
                          reversed_video=list(reversed(frames)))
    return {name: diagnostics(evaluator, base, reference, list(track(images, fps)), spec)
            for name, images in conditions.items()}


def archive_trials(evaluator, archive, scratch):
    from g4_lab.actual import LANDMARK_NAMES

    with ZipFile(archive) as z:
        with z.open('left_1_experiment/baseline_original.mp4') as video:
            path = scratch / 'original.mp4'
            with path.open('xb') as dest:
                shutil.copyfileobj(video, dest)
        data = json.loads(z.read('left_1_experiment/experiment_data.json'))
    info = data['video_info'] | {'frames': data['frames']}
    frames = read_video(path, info)
    prepared = evaluator.call({'op': 'prepare', 'data': data})
    reference = [
        {'t_ms': f['frame_idx'] * 1000 / info['fps'],
         'lm': [[f['landmarks_px'][n]['x'] / info['width'],
                 f['landmarks_px'][n]['y'] / info['height']] for n in LANDMARK_NAMES]
         if f['detected'] else None}
        for f in data['frames']
    ]
    masked = render_masked(frames, data['frames'], 'level3_DIP')
    return {name: trial_pair(evaluator, images, prepared['frames'], reference, info,
                             archive_controls=True)
            for name, images in (('unmasked', frames), ('archive_level3_mask', masked))}


def main():
    import cv2
    import mediapipe as mp

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--archive', type=Path, help='Optional existing left_1_experiment ZIP')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new output path')
    root = args.source_root.resolve()
    cv2.setNumThreads(1)
    with ActualEvaluator(root) as evaluator:
        pool = {}
        thresholds = {source['constants']['THRESHOLD'] for source in evaluator.sources.values()}
        if len(thresholds) != 1:
            raise ValueError('Expected one scorer threshold')
        threshold = thresholds.pop()
        for key, clip in evaluator.clips.items():
            video_path, reference_path = (
                (root / clip[field]).resolve() for field in ('video_file', 'landmarks_file'))
            if not video_path.is_relative_to(root) or not reference_path.is_relative_to(root):
                raise ValueError('Unsafe source manifest')
            data = json.loads(reference_path.read_text(encoding='utf-8'))
            info = data['video_info'] | {'frames': data['frames']}
            frames = read_video(video_path, info)
            source = evaluator.sources[key]
            pool[key] = trial_pair(evaluator, frames, source['base'], source['raw_frames'], info)
        archive = None
        if args.archive:
            with tempfile.TemporaryDirectory(prefix='captcha-camera-controls-') as tmp:
                archive = archive_trials(evaluator, args.archive, Path(tmp))
    report = {
        'scope': 'known_source_offline_pixel_controls', 'python': platform.python_version(),
        'numpy': np.__version__, 'opencv': cv2.__version__, 'mediapipe': mp.__version__,
        'node': subprocess.check_output(['node', '--version'], text=True).strip(),
        'handcaptcha_commit': subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                                                       text=True).strip(),
        'scorer_sha256': hashlib.sha256((root / 'hand_captcha_prod.html').read_bytes()).hexdigest(),
        'timing': 'nominal_frame_index_over_fps', 'score_threshold': threshold,
        'pool': pool, 'paired_archive_one_source': archive,
        'limitations': ['pre-existing masked pool; repeated decoded middle image, not live camera',
                        'one known archive source; same decoded pixels before in-memory masking',
                        'within-clip offline score and gates, no protected action or attacker budget',
                        'no live human, independent test, candidate threshold calibration or model timing']
    }
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
