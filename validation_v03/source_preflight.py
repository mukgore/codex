"""Check private source lineage and exact duplicates before freezing a split."""
import argparse
from collections import Counter
from graphlib import CycleError, TopologicalSorter
import json
from pathlib import Path

from validation_v03.compare_scores import SPLITS
from validation_v03.run_manifest import snapshot_file

FIELDS = {'asset_id', 'source_family_id', 'capture_id', 'performer_id',
          'split', 'parent_asset_ids', 'path'}


def audit(rows, root):
    if not isinstance(rows, list) or not rows:
        raise ValueError('Supply a nonempty array of asset records')
    assets = {}
    groups = {field: {} for field in ('source_family_id', 'capture_id', 'performer_id', 'sha256')}
    findings = Counter()
    for row in rows:
        if not isinstance(row, dict) or row.keys() != FIELDS:
            raise ValueError('Asset record fields do not match the contract')
        for field in FIELDS - {'parent_asset_ids'}:
            value = row[field]
            if not isinstance(value, str) or not value or value != value.strip():
                raise ValueError('Asset record contains an invalid identifier or path')
        parents = row['parent_asset_ids']
        if (not isinstance(parents, list) or len(parents) > 1 or
                any(not isinstance(parent, str) or not parent for parent in parents)):
            raise ValueError('Expected zero or one parent asset ID')
        if row['asset_id'] in assets or row['split'] not in SPLITS:
            raise ValueError('Duplicate asset ID or invalid split')
        relative = Path(row['path'])
        path = (root / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(root):
            raise ValueError('Asset path must resolve inside the private input root')
        digest = snapshot_file(path)['sha256']
        assets[row['asset_id']] = row
        for field, index in groups.items():
            value = digest if field == 'sha256' else row[field]
            index.setdefault(value, set()).add(row['split'])

    # Topological traversal checks all parent references and rejects cycles,
    # including those within a single split.
    graph = TopologicalSorter()
    for asset_id, row in assets.items():
        graph.add(asset_id, *row['parent_asset_ids'])
        for parent_id in row['parent_asset_ids']:
            parent = assets.get(parent_id)
            if parent is None:
                findings['missing_parent_edges'] += 1
                continue
            if parent['split'] != row['split']:
                findings['cross_split_parent_edges'] += 1
            if any(parent[field] != row[field] for field in
                   ('source_family_id', 'capture_id', 'performer_id')):
                findings['inconsistent_parent_lineage_edges'] += 1
    try:
        list(graph.static_order())
    except CycleError:
        findings['lineage_cycle_detected'] = 1

    for field, index in groups.items():
        crossings = sum(len(splits) > 1 for splits in index.values())
        if crossings:
            findings[f'cross_split_{field}_groups'] = crossings
    split_counts = Counter(row['split'] for row in rows)
    for split in SPLITS:
        if not split_counts[split]:
            findings['missing_splits'] += 1
    return {'scope': 'declared_asset_lineage_and_exact_bytes', 'asset_n': len(rows),
            'split_asset_counts': {split: split_counts[split] for split in SPLITS},
            'findings': dict(findings), 'status': 'BLOCKED' if findings else 'PASS'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    try:
        rows = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
        result = audit(rows, args.root.resolve(strict=True))
    except (ValueError, OSError, RuntimeError):
        # File errors and graph errors can contain private paths and IDs.
        parser.exit(2, 'Unable to audit the private inputs. Check manifest format, paths and files.\n')
    print(json.dumps(result, sort_keys=True))
    return int(result['status'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())
