"""Paired cluster bootstrap on held-out attempts with frozen thresholds.

Known shared participants, captures or constituent source families form one
connected cluster. Intervals describe the supplied cluster-resampling model,
not certified population risk or whole-session authentication security.
"""
import math
import numpy as np

from .compare_scores import METRICS, validate_rows


def _clusters(rows):
    parent = list(range(len(rows))); owner = {}
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for index, row in enumerate(rows):
        links = [('source', value.strip()) for value in row['source_family_ids'].split(';')]
        links += [('capture', row['capture_id'].strip())]
        if row['participant_id'].strip(): links += [('participant', row['participant_id'].strip())]
        for link in links:
            if link in owner: parent[find(index)] = find(owner[link])
            else: owner[link] = index
    grouped = {}
    for index, row in enumerate(rows): grouped.setdefault(find(index), []).append(row)
    return list(grouped.values())


def test_intervals(rows, thresholds, *, repetitions, seed, confidence):
    validate_rows(rows)
    if type(repetitions) is not int or not 200 <= repetitions <= 100_000:
        raise ValueError('Explicit 200..100000 bootstrap repetitions required')
    if type(seed) is not int or seed < 0: raise ValueError('Nonnegative integer seed required')
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not .5 < confidence < 1:
        raise ValueError('Finite confidence strictly between .5 and 1 required')
    if set(thresholds) != set(METRICS) or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in thresholds.values()):
        raise ValueError('Both finite frozen validation thresholds required')
    # Thresholds are inputs; no test-set threshold optimization occurs here.
    groups = _clusters([row for row in rows if row['split'] == 'test'])
    if len(groups)*repetitions > 20_000_000:
        raise ValueError('Cluster resampling budget exceeded; reduce repetitions explicitly')
    rng = np.random.default_rng(seed)
    output = {'schema_version': 1, 'split': 'test', 'thresholds': dict(thresholds),
              'method': 'paired_percentile_connected_lineage_cluster_bootstrap',
              'endpoint': 'observed_score_accepts_per_attempt', 'confidence': confidence,
              'repetitions': repetitions, 'seed': seed, 'labels': {},
              'limitations': ['caller-supplied lineage is not independently authenticated',
                             'no joint human/attack confidence statement',
                             'all technical errors and aborts remain in attempt denominators',
                             'no whole-session or protected-action risk guarantee',
                             'few or degenerate clusters cannot bound unseen event risk']}
    alpha = (1-confidence)/2
    for label in ('human', 'attack'):
        subsets = [[row for row in group if row['label'] == label] for group in groups]
        subsets = [group for group in subsets if group]
        counts = np.array([len(group) for group in subsets], dtype=float)
        accepts = np.array([[sum(row['outcome'] == 'scored' and float(row[metric]) >= thresholds[metric] for row in group)
                             for metric in METRICS] for group in subsets], dtype=float)
        observed = accepts.sum(axis=0)/counts.sum()
        result = {'attempted_n': int(counts.sum()), 'cluster_n': len(subsets),
                  'legacy_accepts_per_attempt': float(observed[0]),
                  'candidate_accepts_per_attempt': float(observed[1]),
                  'paired_candidate_minus_legacy': float(observed[1]-observed[0]),
                  'status': 'INSUFFICIENT_CLUSTERS' if len(subsets) < 2 else 'EVALUATED',
                  'intervals': None}
        if len(subsets) >= 2:
            # Bounded rows per iteration; avoid allocating repetitions*clusters.
            samples = np.empty((repetitions, 3))
            for index in range(repetitions):
                chosen = rng.integers(0, len(subsets), size=len(subsets))
                rates = accepts[chosen].sum(axis=0)/counts[chosen].sum()
                samples[index] = (rates[0], rates[1], rates[1]-rates[0])
            result['intervals'] = {}
            for index, name in enumerate(('legacy', 'candidate', 'paired_difference')):
                if np.ptp(samples[:, index]) <= 1e-15:
                    result['intervals'][name] = {'status': 'DEGENERATE_RESAMPLING', 'bounds': None}
                else:
                    bounds = np.quantile(samples[:, index], [alpha, 1-alpha]).tolist()
                    result['intervals'][name] = {'status': 'EVALUATED', 'bounds': bounds}
        output['labels'][label] = result
    return output
