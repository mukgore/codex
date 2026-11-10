"""Build private matched development stimuli from the preserved archive.

Outputs are lossless FFV1 research candidates, never publishable challenges.
Skin ROI must be selected after viewing the representative original frame.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

import cv2
import numpy as np

from analysis.camera_controls import read_video, render_masked


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--ffmpeg', required=True, type=Path)
    p.add_argument('--ffprobe', required=True, type=Path)
    p.add_argument('--skin-roi', required=True, nargs=4, type=int,
                   metavar=('X0', 'Y0', 'X1', 'Y1'))
    args = p.parse_args()
    out = args.output.resolve()
    if (out.exists() or 'private_artifacts' not in out.parts
            or any((parent / '.git').exists() for parent in out.parents)):
        p.error('Use a new private_artifacts directory outside repository/web roots')
    out.mkdir(parents=True)
    with ZipFile(args.archive) as z:
        original = z.read('left_1_experiment/baseline_original.mp4')
        data = json.loads(z.read('left_1_experiment/experiment_data.json'))
    source = out / 'preserved_original.private.mp4'
    source.write_bytes(original)
    info = data['video_info'] | {'frames': data['frames']}
    frames = read_video(source, info)
    x0, y0, x1, y1 = args.skin_roi
    if not (0 <= x0 < x1 <= info['width'] and 0 <= y0 < y1 <= info['height']):
        raise ValueError('Invalid representative-frame skin ROI')
    skin = tuple(int(v) for v in np.median(
        frames[0][y0:y1, x0:x1].reshape(-1, 3), axis=0))
    black = render_masked(frames, data['frames'], 'level3_DIP')
    masks, colored = [], []
    for frame, record in zip(frames, data['frames'], strict=True):
        circle = record['occlusion_levels']['level3_DIP']
        center = tuple(circle['mask_center'][a] for a in ('x', 'y'))
        radius = circle['mask_radius']
        mask = cv2.circle(np.zeros(frame.shape[:2], np.uint8), center, radius, 255, -1) > 0
        masks.append(mask)
        colored.append(cv2.circle(frame.copy(), center, radius, skin, -1))
    results, containers = {}, {}
    for name, images in [('unmasked', frames), ('black', black), ('skin', colored)]:
        path = out / f'{name}.private.mkv'
        command = [str(args.ffmpeg.resolve()), '-v', 'error', '-n', '-f', 'rawvideo',
                   '-pixel_format', 'bgr24', '-video_size', f"{info['width']}x{info['height']}",
                   '-framerate', str(info['fps']), '-i', 'pipe:0', '-an',
                   '-c:v', 'ffv1', '-level', '3', '-pix_fmt', 'bgr0', str(path)]
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for frame in images:
                proc.stdin.write(frame.tobytes())
            proc.stdin.close()
            error = proc.stderr.read().decode('utf-8', 'replace')
            if proc.wait() != 0:
                raise RuntimeError(error)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
        # Decode every final frame, including visible pixels and circle interiors.
        cap = cv2.VideoCapture(str(path))
        count = 0
        try:
            for expected in images:
                ok, decoded = cap.read()
                if not ok or not np.array_equal(decoded, expected):
                    raise ValueError(f'{name}: decoded pixels differ at {count}')
                count += 1
            if cap.read()[0]:
                raise ValueError('Unexpected extra output frame')
        finally:
            cap.release()
        results[name] = {'frames': count, 'decoded_pixel_equality': True,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        container = json.loads(subprocess.check_output([
            str(args.ffprobe.resolve()), '-v', 'error', '-show_streams',
            '-show_frames', '-show_format', '-of', 'json', str(path)]))
        streams = container['streams']
        times = [float(f['best_effort_timestamp_time']) for f in container['frames']]
        if (len(streams) != 1 or streams[0]['codec_type'] != 'video'
                or streams[0]['width'] != info['width']
                or streams[0]['height'] != info['height']
                or len(times) != len(images)
                or any(abs(t - i / info['fps']) > 0.0011 for i, t in enumerate(times))):
            raise ValueError(f'{name}: container stream or timing mismatch')
        containers[name] = {'stream_count': 1, 'frames': len(times),
                            'duration': container['format']['duration'],
                            'all_pts_within_1_1ms_of_i_over_fps': True}
    for raw, b, s, mask in zip(frames, black, colored, masks, strict=True):
        if not (np.array_equal(raw[~mask], b[~mask]) and
                np.array_equal(raw[~mask], s[~mask]) and
                np.all(b[mask] == 0) and np.all(s[mask] == skin)):
            raise ValueError('Mask/visible-region mismatch')
    report = {'source_sha256': hashlib.sha256(original).hexdigest(),
              'source_families': 1, 'split': 'known_development_only',
              'rights_status': 'UNREVIEWED', 'release_allowed': False,
              'width': info['width'], 'height': info['height'], 'fps': info['fps'],
              'frames': len(frames), 'duration_seconds': len(frames) / info['fps'],
              'mask': 'archived level3_DIP, same circle per corresponding frame, opaque',
              'skin_bgr': skin, 'skin_reference_frame': 0, 'skin_roi_xyxy': args.skin_roi,
              'skin_rule': 'fixed per-clip median BGR in manually chosen finger ROI',
              'encoding': 'same FFV1 level3 bgr0 Matroska, no audio',
              'conditions': results, 'all_frame_mask_and_visible_region_checks': True,
              'limitations': ['Engineering development fixture; no human/model comparison.',
                              'Archived circles are not anatomical concealment approval.',
                              'Not an independent source or measured landmark ground truth.',
                              'Container PTS and tracks require independent ffprobe check.']}
    (out / 'pair.private.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out / 'container_checks.private.json').write_text(
        json.dumps(containers, indent=2) + '\n', encoding='utf-8')
    tiles = []
    for images in [frames, black, colored]:
        tiles.append(cv2.hconcat([cv2.resize(images[i], (240, 240))
                                 for i in [0, len(frames)//2, len(frames)-1]]))
    ok, encoded = cv2.imencode('.jpg', cv2.vconcat(tiles))
    if not ok:
        raise ValueError('Contact sheet encoding failed')
    (out / 'contact.private.jpg').write_bytes(encoded.tobytes())
    print(json.dumps({'conditions': len(results), 'frames_each': len(frames),
                      'all_pixels_verified': True, 'release_allowed': False}))


if __name__ == '__main__':
    main()
