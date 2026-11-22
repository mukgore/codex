"""Export the independently sourced clips with the benchmark occlusion applied."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

from external_hand_verification import H, MASK_R, MASK_X, MASK_Y, SEQUENCES, W, read_clip


def export(data_root: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for existing in (output_dir / 'index.json', output_dir / 'README.md'):
        if existing.exists():
            raise FileExistsError(existing)
    index = []
    for session, side, stem in SEQUENCES:
        clip = read_clip(data_root, session, side, stem)
        target = output_dir / f'{stem}_occluded.mp4'
        if target.exists():
            raise FileExistsError(target)
        writer = cv2.VideoWriter(str(target), cv2.VideoWriter_fourcc(*'mp4v'),
                                 float(clip['fps']), (W, H))
        if not writer.isOpened():
            raise OSError(f'cannot create preview: {target}')
        try:
            for frame in clip['masked_rgb']:
                writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        finally:
            writer.release()
        index.append({
            'video': target.name, 'source': str(clip['video_path']),
            'session': session, 'side': side, 'frames': clip['frames'],
            'fps': clip['fps'], 'duration_seconds': clip['duration_seconds'],
            'source_resolution': [clip['source_width'], clip['source_height']],
            'canonical_resolution': [W, H], 'mask': clip['mask'],
            'letterbox': clip['letterbox'], 'video_sha256': clip['video_sha256'],
            'label_sha256': clip['label_sha256'],
            'hidden_rule': f'annotated point center distance <= {MASK_R}px from ({MASK_X},{MASK_Y})',
        })
    (output_dir / 'index.json').write_text(json.dumps(index, indent=2), encoding='utf-8')
    (output_dir / 'README.md').write_text(
        '# Occlusion previews\n\n'
        'GigaHands demo clips transformed to 512 x 420 with the original fixed '
        'RGB(7,11,16) circular occluder applied to every frame. Source annotations were '
        'transformed using the same contain geometry. Dataset and preview files '
        'remain outside Git. GigaHands demo data is CC BY-NC 4.0.\n',
        encoding='utf-8')
    print(f'Exported {len(index)} masked previews to {output_dir}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    export(args.data_root, args.output_dir)


if __name__ == '__main__':
    main()
