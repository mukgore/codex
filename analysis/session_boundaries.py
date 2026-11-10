"""Reconstruct saved segment/log correspondence without guessing video-play gates."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import statistics


def reconstruct(data):
    logs, segments = data['sessionLog'], data['segments']
    flat = [frame for segment in segments for frame in segment['frames']]
    indices = [i for i, frame in enumerate(logs) if frame['phase'] == 'recording']
    if not indices or indices[0] == 0:
        raise ValueError('No preceding matching event')
    mapped = [indices[0] - 1] + indices
    if (logs[mapped[0]]['phase'] != 'matching' or len(mapped) != len(flat)
            or any(frame['lm'] != logs[index]['lm'] for frame, index in zip(flat, mapped))):
        raise ValueError('Coordinate sequence correspondence not established')
    rows, position = [], 0
    for segment in segments:
        frames = segment['frames']
        if not frames or any(b['t'] <= a['t'] for a, b in zip(frames, frames[1:])):
            raise ValueError('Invalid segment timeline')
        chosen = mapped[position:position + len(frames)]
        offsets = [logs[i]['t'] - frame['t'] for i, frame in zip(chosen, frames)]
        rows.append({'segment_index': len(rows), 'frames': len(frames),
                     'log_index_start': chosen[0], 'log_index_end': chosen[-1],
                     'first_logged_phase': logs[chosen[0]]['phase'],
                     'relative_segment_end_ms': frames[-1]['t'],
                     'stored_duration_ms': segment['duration'],
                     'offset_median_ms': statistics.median(offsets),
                     'offset_span_ms': max(offsets) - min(offsets),
                     'exact_coordinate_sequence': True,
                     'playback_wait_boundary_verified': False})
        position += len(frames)
    return {'segment_frames': len(flat), 'log_recording_frames': len(indices),
            'phase_counts': dict(collections.Counter(f['phase'] for f in logs)),
            'segments': rows, 'full_log_span_seconds': (logs[-1]['t']-logs[0]['t'])/1000,
            'segment_duration_sum_seconds': sum(s['duration'] for s in segments)/1000,
            'missing_segment_frames': sum(f['lm'] is None for f in flat)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw-root', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    out = args.output.resolve()
    if (out.exists() or 'private_artifacts' not in out.parts
            or any((parent/'.git').exists() for parent in out.parents)):
        p.error('New private directory outside repositories required')
    paths = sorted(args.raw_root.glob('2*/2*/*.json'))
    if not paths:
        p.error('No saved sessions found')
    out.mkdir(parents=True)
    rows, failures = [], []
    for path in paths:
        raw = path.read_bytes()
        try:
            rows.append({'source_sha256': hashlib.sha256(raw).hexdigest(),
                         **reconstruct(json.loads(raw.decode('utf-8-sig')))})
        except (ValueError, KeyError, TypeError) as exc:
            failures.append({'source_sha256': hashlib.sha256(raw).hexdigest(), 'reason': str(exc)})
    summary = {'sessions_attempted': len(paths), 'sessions_exactly_mapped': len(rows),
               'sessions_unmapped': len(failures),
               'segments_mapped': sum(len(r['segments']) for r in rows),
               'segment_frames': sum(r['segment_frames'] for r in rows),
               'recording_log_frames': sum(r['log_recording_frames'] for r in rows),
               'extra_initial_matching_frames': len(rows),
               'missing_segment_frames': sum(r['missing_segment_frames'] for r in rows),
               'max_segment_offset_span_ms': max(
                   (s['offset_span_ms'] for r in rows for s in r['segments']), default=None),
               'continuous_motion_interpretation_allowed': False,
               'limitations': ['No videoPlaying/fading/gate events in saved log.',
                               'Coordinate correspondence does not recover historical build.',
                               'Browser callback clocks differ; no frame capture time inferred.']}
    for filename, obj in [('sessions.private.json', {'rows': rows, 'failures': failures}),
                          ('summary.json', summary)]:
        (out/filename).write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
