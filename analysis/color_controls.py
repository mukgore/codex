"""CPU MediaPipe comparison on matched private stimuli; no independent truth claim."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import statistics
import sys
import time
from zipfile import ZipFile

import cv2
import numpy as np

from analysis.camera_controls import diagnostics, adapted
from g4_lab.actual import ActualEvaluator, LANDMARK_NAMES
from validation_v03.adapters import InputSpec


def disagreements(frames, reference, records, width, height):
    values = {'visible': [], 'hidden': []}
    possible = {'visible': 0, 'hidden': 0}
    for frame, ref, record in zip(frames, reference, records, strict=True):
        if ref['lm'] is None:
            continue
        mask = record['occlusion_levels']['level3_DIP']
        center = np.array([mask['mask_center'][a] for a in ('x', 'y')])
        for index, point in enumerate(ref['lm']):
            px = np.array(point) * [width, height]
            group = 'hidden' if np.linalg.norm(px-center) <= mask['mask_radius'] else 'visible'
            possible[group] += 1
            if frame['lm'] is not None:
                error = np.linalg.norm(np.array(frame['lm'][index])*[width,height]-px)
                values[group].append(float(error))
    return {group: {'reference_points': possible[group], 'compared_points': len(errors),
                    'mean_distance_pixels_on_compared_points': statistics.mean(errors) if errors else None}
            for group, errors in values.items()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', required=True, type=Path)
    p.add_argument('--archive', required=True, type=Path)
    p.add_argument('--pair-root', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--repetitions', type=int, default=3)
    args = p.parse_args()
    out = args.output.resolve()
    if (out.exists() or 'private_artifacts' not in out.parts
            or any((parent/'.git').exists() for parent in out.parents)
            or not 1 <= args.repetitions <= 10):
        p.error('New private output and 1..10 repetitions required')
    pair = json.loads((args.pair_root/'pair.private.json').read_text(encoding='utf-8'))
    with ZipFile(args.archive) as archive:
        original = archive.read('left_1_experiment/baseline_original.mp4')
        data = json.loads(archive.read('left_1_experiment/experiment_data.json'))
    if hashlib.sha256(original).hexdigest() != pair['source_sha256']:
        raise ValueError('Archive does not match paired source')
    root = args.source_root.resolve()
    sys.path.insert(0, str(root))
    from dataset_pipeline.stage1_extract import extract_landmarks
    out.mkdir(parents=True)
    versions = {name:importlib.metadata.version(name) for name in ['mediapipe','numpy','protobuf']}
    versions['opencv_runtime'] = cv2.__version__
    width, height, fps = pair['width'], pair['height'], pair['fps']
    reference = [{'t_ms': f['frame_idx']*1000/fps,
                  'lm': [[f['landmarks_px'][name][axis]/size for axis, size in [('x',width),('y',height)]]
                         for name in LANDMARK_NAMES] if f['detected'] else None}
                 for f in data['frames']]
    spec = InputSpec(width,height,'normalized_xy','ms',False,2/fps)
    adapted_reference = adapted(reference,spec)
    results, samples, failures = [], {}, []
    with ActualEvaluator(root) as evaluator:
        base = evaluator.call({'op':'prepare','data':data})['frames']
        for repetition in range(args.repetitions):
            # Rotate order to reduce always running unmasked first; no cold-cache claim.
            conditions = ['unmasked','black','skin']
            conditions = conditions[repetition % 3:] + conditions[:repetition % 3]
            for condition in conditions:
                path = args.pair_root/f'{condition}.private.mkv'
                if hashlib.sha256(path.read_bytes()).hexdigest() != pair['conditions'][condition]['sha256']:
                    raise ValueError('Paired final video changed')
                start = time.perf_counter()
                try:
                    raw, info = extract_landmarks(str(path.resolve()), worker_timeout_seconds=45)
                    elapsed = time.perf_counter()-start
                    if (len(raw) != pair['frames'] or not info['timestamps_monotonic']
                            or any(f['frame_idx'] != i for i, f in enumerate(raw))):
                        raise ValueError('Frame denominator or timeline mismatch')
                    frames = [{'t_ms': i*1000/fps,
                               'lm': [[f['landmarks_px'][name][axis]/size
                                       for axis,size in [('x',width),('y',height)]]
                                      for name in LANDMARK_NAMES] if f['detected'] else None}
                              for i,f in enumerate(raw)]
                    samples[f'{repetition}/{condition}'] = frames
                    metric = diagnostics(evaluator,base,adapted_reference,frames,spec)
                    results.append({'condition': condition,'repetition': repetition,
                                    'batch_seconds_including_resource_worker': elapsed,
                                    'legacy_and_candidate': metric,
                                    'archive_mediapipe_disagreement': disagreements(
                                        frames,reference,data['frames'],width,height)})
                    (out/f'run_{repetition}_{condition}.private.json').write_text(
                        json.dumps({'frames': frames, 'result': results[-1]}, allow_nan=False)+'\n',
                        encoding='utf-8')
                except (RuntimeError, TimeoutError, ValueError) as exc:
                    failures.append({'condition':condition,'repetition':repetition,
                                     'elapsed_seconds':time.perf_counter()-start,'error_type':type(exc).__name__})
    summary = {'scope':'one_known_source_matched_color_development_diagnostic',
               'attempted_batches':3*args.repetitions,'completed_batches':len(results),
               'failures':failures,'frames_per_batch':pair['frames'], 'versions':versions,
               'coordinate_time':'nominal i/fps; final container PTS separately verified within 1.1ms',
               'condition_runs':results,
               'limitations':['No independent human landmark truth; distances are tracker disagreements.',
                              'Visibility groups use archived estimated locations, not independent annotation.',
                              'Batch time includes imports/resource copying/decoding; not per-frame or request latency.',
                              'Repetitions share one source and are not independent trials.',
                              'No live camera, human interpretation, HaMeR, calibration or authentication efficacy.']}
    for filename,obj in [('coordinates.private.json',samples),('summary.json',summary)]:
        (out/filename).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'attempted_batches':3*args.repetitions,'completed_batches':len(results),'failures':len(failures)}))


if __name__ == '__main__':
    main()
