"""Merge disjoint RGB/annotation exports while rejecting duplicate sources."""

import argparse
import json
from pathlib import Path
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, nargs='+', required=True)
    parser.add_argument('--include-seeds', nargs='+', metavar='START-END')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir()
    clips, names, seed_groups = [], set(), set()
    shape = None
    included = None
    if args.include_seeds:
        included = set()
        for value in args.include_seeds:
            start, end = (int(part) for part in value.split('-', 1))
            if start > end:
                raise ValueError(f'Invalid seed range: {value}')
            included.update(range(start, end + 1))
    for root in args.inputs:
        manifest = json.loads((root / 'annotations.json').read_text(encoding='utf8'))
        current_shape = (manifest['width'], manifest['height'])
        if shape is not None and shape != current_shape:
            raise ValueError(f'Incompatible frame sizes: {shape} and {current_shape}')
        shape = current_shape
        selected_clips = [clip for clip in manifest['clips']
                          if included is None or int(clip['source'].split('-')[1]) in included]
        current_seeds = {int(clip['source'].split('-')[1]) for clip in selected_clips}
        overlap = current_seeds & seed_groups
        if overlap:
            raise ValueError(f'Generator seeds appear in multiple inputs: {sorted(overlap)}')
        seed_groups.update(current_seeds)
        for clip in selected_clips:
            if clip['name'] in names:
                raise ValueError(f'Duplicate clip in inputs: {clip["name"]}')
            source = root / (clip['name'] + '.rgb')
            if not source.is_file():
                raise FileNotFoundError(source)
            shutil.copy2(source, args.output / source.name)
            clips.append(clip)
            names.add(clip['name'])
    out = {'width': shape[0], 'height': shape[1], 'clips': clips}
    (args.output / 'annotations.json').write_text(json.dumps(out), encoding='utf8')
    print(json.dumps({'clips': len(clips), 'generator_seeds': len(seed_groups), 'width': shape[0], 'height': shape[1]}))


if __name__ == '__main__':
    main()
