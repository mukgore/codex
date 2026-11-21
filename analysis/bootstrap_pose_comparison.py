"""Paired, generator-seed-cluster bootstrap for a matched HaMeR report."""

import argparse
import json
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--draws', type=int, default=20000)
    parser.add_argument('--seed', type=int, default=20261121)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding='utf8'))
    random = np.random.default_rng(args.seed)
    result = {'method': 'paired bootstrap over independent generator seeds; clips within seed stay together',
              'draws': args.draws, 'domains': {}}
    for mode, row in report['domains'].items():
        local = {clip['name']: clip for clip in row['selected']['per_clip']}
        hamer = {clip['name']: clip for clip in row['hamer']['per_clip']}
        if local.keys() != hamer.keys():
            raise ValueError(f'Matched frame lists differ for {mode}')
        grouped = {}
        for name in local:
            source = local[name]['source']
            cluster = source.split('-')[1] if mode in ('2d', '3d') else source
            grouped.setdefault(cluster, []).append((local[name], hamer[name]))
        clusters = []
        for cluster, pairs in sorted(grouped.items()):
            local_nme = float(np.mean([a['nme'] for a, _ in pairs]))
            hamer_nme = float(np.mean([b['nme'] for _, b in pairs]))
            local_pck = float(np.mean([a['pck_20'] for a, _ in pairs]))
            hamer_pck = float(np.mean([b['pck_20'] for _, b in pairs]))
            local_hidden = [a['hidden_nme'] for a, _ in pairs if a['hidden_nme'] is not None]
            hamer_hidden = [b['hidden_nme'] for _, b in pairs if b['hidden_nme'] is not None]
            clusters.append({'key': cluster, 'local_nme': local_nme, 'hamer_nme': hamer_nme,
                             'local_pck_20': local_pck, 'hamer_pck_20': hamer_pck,
                             'local_hidden_nme': float(np.mean(local_hidden)) if local_hidden else None,
                             'hamer_hidden_nme': float(np.mean(hamer_hidden)) if hamer_hidden else None})
        if len(clusters) < 2:
            raise ValueError(f'Need at least two independent clusters for {mode}')
        draws = random.integers(0, len(clusters), size=(args.draws, len(clusters)))
        local_nme = np.asarray([c['local_nme'] for c in clusters])[draws].mean(axis=1)
        hamer_nme = np.asarray([c['hamer_nme'] for c in clusters])[draws].mean(axis=1)
        delta_pck = (np.asarray([c['local_pck_20'] for c in clusters])[draws]
                     - np.asarray([c['hamer_pck_20'] for c in clusters])[draws]).mean(axis=1)
        result['domains'][mode] = {
            'independent_clusters': len(clusters),
            'local_nme': float(np.mean([c['local_nme'] for c in clusters])),
            'hamer_nme': float(np.mean([c['hamer_nme'] for c in clusters])),
            'nme_reduction_fraction': float(1 - np.mean([c['local_nme'] for c in clusters])
                                            / np.mean([c['hamer_nme'] for c in clusters])),
            'nme_reduction_95_ci': [float(np.quantile(1 - local_nme / hamer_nme, q)) for q in (.025, .975)],
            'pck_20_gain': float(np.mean([c['local_pck_20'] - c['hamer_pck_20'] for c in clusters])),
            'pck_20_gain_95_ci': [float(np.quantile(delta_pck, q)) for q in (.025, .975)],
            'per_cluster': clusters,
        }
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf8')
    print(json.dumps({domain: {key: value for key, value in row.items() if key != 'per_cluster'}
                      for domain, row in result['domains'].items()}))


if __name__ == '__main__':
    main()
