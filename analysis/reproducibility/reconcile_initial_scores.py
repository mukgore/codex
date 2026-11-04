"""Replay the historical initial-score candidates without executing archived code.

Inputs are read only. Only cohort/level aggregates go to --summary; all paths,
hashes, session/action summaries and trial comparisons go to --private-dir.
Historical formulas are explicit candidates, not inferred collection builds.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import scipy
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter
from scipy.stats import pearsonr

NAMES = ['WRIST', 'THUMB_CMC', 'THUMB_MCP', 'THUMB_IP', 'THUMB_TIP',
         'INDEX_MCP', 'INDEX_PIP', 'INDEX_DIP', 'INDEX_TIP',
         'MIDDLE_MCP', 'MIDDLE_PIP', 'MIDDLE_DIP', 'MIDDLE_TIP',
         'RING_MCP', 'RING_PIP', 'RING_DIP', 'RING_TIP',
         'PINKY_MCP', 'PINKY_PIP', 'PINKY_DIP', 'PINKY_TIP']
ANGLES = [(0, 1, 2), (1, 2, 3), (2, 3, 4), (0, 5, 6), (5, 6, 7),
          (6, 7, 8), (0, 9, 10), (9, 10, 11), (10, 11, 12),
          (0, 13, 14), (13, 14, 15), (14, 15, 16), (0, 17, 18),
          (17, 18, 19), (18, 19, 20)]
PAIRS15 = [(5, 6), (6, 7), (7, 8), (9, 10), (10, 11), (11, 12),
           (13, 14), (14, 15), (15, 16), (17, 18), (18, 19), (19, 20),
           (1, 2), (2, 3), (3, 4)]
PAIRS21 = PAIRS15 + [(4, 8), (8, 12), (12, 16), (16, 20), (4, 20), (8, 20)]
MAXIMA = dict(angle=39.1673, dtw_angle=32.6513, tendency=0.78,
              accel=0.0237, distance=0.524, dtw_distance=0.532, trajectory=1.4948)
WEIGHTS = dict(dtw_angle=0.44, angle=0.31, tendency=0.25)
TABLE7 = {
    1: dict(distance=.219, dtw_distance=.263, angle=.564, dtw_angle=.796,
            accel=.335, tendency=.356, trajectory=.282),
    2: dict(distance=.265, dtw_distance=.345, angle=.538, dtw_angle=.791,
            accel=.236, tendency=.453, trajectory=.262),
    3: dict(distance=.270, dtw_distance=.311, angle=.464, dtw_angle=.747,
            accel=.286, tendency=.337, trajectory=.276),
}
FLOAT_ATOL = 1e-8
DISPLAY_ATOL = 0.0005


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def payload_digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode('utf-8')).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
                    + '\n', encoding='utf-8')


def preprocess(frames):
    arr = np.asarray(frames, dtype=float)
    if not len(arr):
        return None
    if arr.ndim != 3 or arr.shape[1] != 21 or arr.shape[2] < 2:
        raise ValueError('Expected frame x 21 x coordinates')
    if not np.isfinite(arr).all():
        raise ValueError('Nonfinite coordinates')
    if len(arr) < 3:
        return None
    arr = arr[:, :, :2].copy()
    arr -= arr[:, :1, :]
    scale = np.linalg.norm(arr[:, 9, :], axis=1)[:, None, None]
    return arr / np.maximum(scale, 1e-6)


def resample(arr, length):
    if arr is None or len(arr) < 3:
        return None
    if len(arr) == length:
        return arr
    return interp1d(np.linspace(0, 1, len(arr)), arr, axis=0)(np.linspace(0, 1, length))


def dtw_path(a, b):
    """Unconstrained absolute-cost DTW; backtrack ties diagonal, up, left.

    Return aligned index pairs, not accumulated cost/path length. The latter
    would change the historical mean angle error being reproduced.
    """
    n, m = len(a), len(b)
    cost = np.full((n + 1, m + 1), np.inf)
    cost[0, 0] = 0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost[i, j] = abs(a[i-1] - b[j-1]) + min(
                cost[i-1, j], cost[i, j-1], cost[i-1, j-1])
    ia, ib = [], []
    i, j = n, m
    while i > 0 and j > 0:
        ia.append(i-1)
        ib.append(j-1)
        _, i, j = min([(cost[i-1, j-1], i-1, j-1),
                       (cost[i-1, j], i-1, j),
                       (cost[i, j-1], i, j-1)], key=lambda t: t[0])
    return np.array(ia[::-1]), np.array(ib[::-1])


def joint_angles(arr):
    result = []
    for p, j, d in ANGLES:
        a, b = arr[:, p] - arr[:, j], arr[:, d] - arr[:, j]
        ratio = np.sum(a*b, axis=1) / (
            np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1) + 1e-8)
        result.append(np.degrees(np.arccos(np.clip(ratio, -1, 1))))
    return result


def tendency(user_resampled, base, pairs):
    correlations = []
    for a, b in pairs:
        x = np.linalg.norm(base[:, a] - base[:, b], axis=1)
        y = np.linalg.norm(user_resampled[:, a] - user_resampled[:, b], axis=1)
        r = 0.0 if min(np.std(x), np.std(y)) < 1e-8 else pearsonr(x, y)[0]
        correlations.append(float(r) if np.isfinite(r) else 0.0)
    return float(np.mean(correlations))


def raw_metrics(user, base):
    if user is None or base is None:
        return {**dict.fromkeys(MAXIMA), 'tendency21': None}
    tr = resample(user, len(base))
    ba, ta, ua = joint_angles(base), joint_angles(tr), joint_angles(user)
    aligned = []
    for b, u in zip(ba, ua):
        ib, iu = dtw_path(b, u)
        aligned.append(np.mean(np.abs(b[ib] - u[iu])))
    # Preserve NumPy's flattened accumulation, relevant to near-tied DTW paths.
    ib, iu = dtw_path(np.mean(base[:, 1:], axis=(1, 2)),
                      np.mean(user[:, 1:], axis=(1, 2)))
    # Prior JavaScript replay sums each x+y pair before summing landmarks.
    # Tiny accumulation differences can select a different tied DTW path.
    jb, ju = dtw_path(
        [sum(float(p[0]+p[1]) for p in f[1:])/40 for f in base],
        [sum(float(p[0]+p[1]) for p in f[1:])/40 for f in user])
    accel = None if len(base) < 5 else float(np.mean(np.abs(
        np.linalg.norm(np.diff(base[:, 1:], n=2, axis=0), axis=2) -
        np.linalg.norm(np.diff(tr[:, 1:], n=2, axis=0), axis=2))))
    trajectory = None
    if len(user) >= 10:
        window = int(len(user)*.25)
        window += window % 2 == 0
        window = max(window, 5)
        if window >= len(user):
            window = len(user)-1 if (len(user)-1) % 2 else len(user)-2
        smooth = savgol_filter(user[:, 1:], window, 3, axis=0)
        deviation = np.linalg.norm(user[:, 1:] - smooth, axis=2)
        means = deviation.mean(axis=0)
        trajectory = float(np.mean(np.divide(deviation.std(axis=0), means,
            out=np.zeros_like(means), where=means > 1e-8)))
    return dict(angle=float(np.mean([np.mean(np.abs(b-t)) for b, t in zip(ba, ta)])),
                dtw_angle=float(np.mean(aligned)), tendency=tendency(tr, base, PAIRS15),
                tendency21=tendency(tr, base, PAIRS21),
                distance=float(np.mean(np.linalg.norm(base[:, 1:]-tr[:, 1:], axis=2))),
                dtw_distance=float(np.mean(np.linalg.norm(base[ib, 1:]-user[iu, 1:], axis=2))),
                dtw_distance_js_accumulation=float(np.mean(np.linalg.norm(base[jb, 1:]-user[ju, 1:], axis=2))),
                accel=accel, trajectory=trajectory)


def estimate(raw, metric, detection_rate, clipped=True):
    if raw is None:
        return 0.0
    value = raw/MAXIMA[metric] if metric == 'tendency' else 1-raw/MAXIMA[metric]
    if clipped:
        value = np.clip(value, 0, 1)
    value = detection_rate*value
    return float(np.clip(value, 0, 1) if clipped else value)


def weighted(metrics):
    return float(sum(w*metrics[m] for m, w in WEIGHTS.items()))


def scores_for(row, pairs=15):
    return {m: estimate(row['raw']['tendency21' if pairs == 21 and m == 'tendency' else m],
                        m, row['detection_rate']) for m in MAXIMA}


def summarize(rows, pairs):
    metric_means = {m: float(np.mean([scores_for(r, pairs)[m] for r in rows])) for m in MAXIMA}
    values = np.array([weighted(scores_for(r, pairs)) for r in rows])
    by_session = defaultdict(list)
    for row, value in zip(rows, values):
        by_session[row['session']].append(value)
    mean = float(values.mean())
    return dict(trials=len(rows), metric_means=metric_means, trial_equal_score=mean,
                session_equal_score=float(np.mean([np.mean(v) for v in by_session.values()])),
                frame_weighted_score=float(np.average(values, weights=[r['total_frames'] for r in rows])),
                mean_weighted_minus_weighted_mean=mean-weighted(metric_means))


def table7_path(rows, pairs=21):
    """occlusion_estimation_score.py: average raw by hand/action, human dr=1.

    Uses archived rounded maxima; original dynamic maxima cannot be recovered
    without the original MediaPipe coordinate inputs. No clipping in this path.
    """
    cells = defaultdict(list)
    for r in rows:
        cells[r['action']].append(r)
    cell_scores = []
    for values in cells.values():
        means = {}
        for m in MAXIMA:
            key = 'tendency21' if pairs == 21 and m == 'tendency' else m
            valid = [r['raw'][key] for r in values if r['raw'][key] is not None]
            means[m] = estimate(float(np.mean(valid)) if valid else None, m, 1.0, False)
        cell_scores.append(means)
    means = {m: float(np.mean([s[m] for s in cell_scores])) for m in MAXIMA}
    return dict(action_cells=len(cells), metric_means=means, score=weighted(means),
                mean_weighted_minus_weighted_mean=float(np.mean([weighted(s) for s in cell_scores]))-weighted(means))


def trial21_unclipped(rows, use_recorded_detection=True):
    values = []
    for row in rows:
        dr = row['detection_rate'] if use_recorded_detection else 1.0
        values.append(weighted({m: estimate(row['raw']['tendency21' if m == 'tendency' else m],
                                             m, dr, False) for m in WEIGHTS}))
    return float(np.mean(values))


def load_cohort(paths, baseline):
    rows, inputs, seen_payloads, participants = [], [], {}, set()
    duplicate_count = 0
    for index, path in enumerate(paths, 1):
        data = read_json(path)
        trials = data['trials']
        info = data['experimentInfo']
        alias = f'session-{index:02d}'
        fingerprint = payload_digest(trials)
        # Collapse only re-exports with identical observations and metadata
        # except completion time. Same ID with new measurements is retained.
        duplicate_key = payload_digest([trials, {k: v for k, v in info.items() if k != 'completedAt'}])
        duplicate_of = seen_payloads.get(duplicate_key)
        inputs.append(dict(alias=alias, path=str(Path(path).resolve()), sha256=digest(path),
                           participant_id=info['participantId'], hand=info['selectedHand'],
                           completed_at=info.get('completedAt'), version=info.get('version'),
                           trial_payload_sha256=fingerprint, duplicate_of=duplicate_of))
        if duplicate_of:
            duplicate_count += 1
            continue
        seen_payloads[duplicate_key] = alias
        participants.add(info['participantId'])
        cells = [(t['action'], t['level']) for t in trials]
        if Counter(cells) != Counter((a, lv) for a in (1, 2, 3) for lv in (1, 2, 3)):
            raise ValueError('Cohort must have one trial per action x level per session')
        for t in trials:
            action = t['videoId'].split('_')[0]
            if action != ('l' if info['selectedHand'] == 'left' else 'r')+str(t['action']):
                raise ValueError('Hand/action mapping mismatch')
            frames = t['frames']
            valid = [f['landmarks'] for f in frames if f['landmarks'] is not None]
            if len(frames) != t['totalFrames'] or len(valid) != t['detectedFrames']:
                raise ValueError('Frame payload/metadata counts differ')
            total = t['totalFrames']
            raw = raw_metrics(preprocess(valid), baseline[action])
            rows.append(dict(session=alias, participant_id=info['participantId'],
                             hand=info['selectedHand'], action=action, level=t['level'],
                             video_id=t['videoId'], total_frames=total, valid_frames=len(valid),
                             detection_rate=len(valid)/total if total else 0.0,
                             raw=raw, historical_saved_metrics=None))
    counts = dict(input_files=len(paths), unique_trial_payloads=len(seen_payloads),
                  duplicate_payload_files=duplicate_count, unique_recorded_participant_ids=len(participants),
                  trials=len(rows), frame_records=sum(r['total_frames'] for r in rows),
                  coordinate_frames=sum(r['valid_frames'] for r in rows))
    counts['null_frames'] = counts['frame_records']-counts['coordinate_frames']
    return rows, inputs, counts


def cohort_summary(rows, counts):
    levels = {}
    for lv in (1, 2, 3):
        subset = [r for r in rows if r['level'] == lv]
        levels[str(lv)] = dict(verified_final_15=summarize(subset, 15),
                               grid_definition_21=summarize(subset, 21),
                               table7_candidate_21=table7_path(subset))
    return dict(counts=counts, levels=levels, overall_verified_final_15=summarize(rows, 15),
                overall_grid_definition_21=summarize(rows, 21),
                overall_table7_candidate_score=float(np.mean([
                    levels[str(lv)]['table7_candidate_21']['score'] for lv in (1, 2, 3)])))


def compare_previous(rows, csv_path):
    previous = list(csv.DictReader(Path(csv_path).open(encoding='utf-8-sig', newline='')))
    comparisons = []
    errors = defaultdict(list)
    accumulation_errors, accumulation_changed = [], 0
    if len(previous) != len(rows):
        raise ValueError('Previous replay row count differs')
    for row in rows:
        alias = 'legacy-'+row['session'].split('-')[-1]
        matches = [p for p in previous if p['session_alias'] == alias and
                   p['action'] == row['action'] and int(float(p['level'])) == row['level']]
        if len(matches) != 1:
            raise ValueError('Previous replay session/action/level mapping is ambiguous')
        old = matches[0]
        alternate = row['raw']['dtw_distance_js_accumulation']
        accumulation_errors.append(abs(alternate-float(old['raw_dtw_distance'])))
        accumulation_changed += abs(alternate-row['raw']['dtw_distance']) > FLOAT_ATOL
        deltas = {}
        for m in MAXIMA:
            deltas['raw_'+m] = row['raw'][m]-float(old['raw_'+m])
            deltas['estimated_'+m] = scores_for(row)[m]-float(old['estimated_'+m])
        deltas['score'] = weighted(scores_for(row))-float(old['legacy_captcha_score'])
        for key, delta in deltas.items():
            errors[key].append(abs(delta))
        comparisons.append(dict(session=row['session'], action=row['action'], level=row['level'], deltas=deltas))
    return dict(rows=len(rows), reference='prior independent JavaScript replay, not historical stored scores',
                max_abs_delta={k: max(v) for k, v in errors.items()},
                dtw_distance_accumulation_diagnostic=dict(
                    changed_rows=int(accumulation_changed),
                    alternate_js_order_max_abs_delta=max(accumulation_errors),
                    composite_affected=False,
                    definition='sum each x+y pair then landmarks, versus flattened NumPy mean'),
                all_within_atol=all(max(v) <= FLOAT_ATOL for v in errors.values())), comparisons


def inspect_workbook(rows, path):
    # Read cached data and formulas separately; never save or recalculate inputs.
    import openpyxl
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    formulas = openpyxl.load_workbook(path, read_only=True, data_only=False)
    details, comparisons, displayed = [], [], []
    for values in list(book['개별_분포'].values)[1:]:
        if values[0] != '사람':
            continue
        prefix, action = values[1].split('/')
        matches = [r for r in rows if r['participant_id'].startswith(prefix)
                   and r['action'] == action and r['level'] == 3]
        if len(matches) != 1:
            raise ValueError('Workbook detail mapping is ambiguous')
        row = matches[0]
        delta = {}
        for pairs in (15, 21):
            scores = scores_for(row, pairs)
            delta[str(pairs)] = dict(score=weighted(scores)-values[2],
                dtw_angle=scores['dtw_angle']-values[3], angle=scores['angle']-values[4],
                tendency=scores['tendency']-values[5])
        comparisons.append(dict(session=row['session'], action=action, deltas=delta))
        displayed.append(values[2])
    for pairs in ('15', '21'):
        maxima = {m: max(abs(r['deltas'][pairs][m]) for r in comparisons)
                  for m in ('score', 'dtw_angle', 'angle', 'tendency')}
        details.append(dict(pair_count=int(pairs), max_abs_display_delta=maxima,
                            all_within_display_tolerance=all(v <= DISPLAY_ATOL for v in maxima.values())))
    aggregate_rows = list(book['3자_비교'].values)[1:]
    saved_aggregate = next(v[1] for v in aggregate_rows if v[0] == 'CAPTCHA')
    formula_count = sum(isinstance(c.value, str) and c.value.startswith('=')
                        for s in formulas for row in s for c in row)
    book.close()
    formulas.close()
    return dict(human_detail_rows=len(comparisons), displayed_human_detail_score_mean=float(np.mean(displayed)),
                displayed_comparison_score=saved_aggregate,
                comparison_minus_detail_mean=saved_aggregate-float(np.mean(displayed)),
                workbook_formula_count=formula_count, detail_comparisons=details), comparisons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--sessions', type=Path, nargs='+', required=True,
                        help='Ordered as in the archived source; private paths only')
    parser.add_argument('--candidate-sessions', type=Path, nargs='*', default=[])
    parser.add_argument('--previous-csv', type=Path)
    parser.add_argument('--comparison-workbook', type=Path)
    parser.add_argument('--evidence-files', type=Path, nargs='*', default=[])
    parser.add_argument('--private-dir', type=Path, required=True)
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    if args.summary.resolve() == args.private_dir.resolve() or args.private_dir.resolve() in args.summary.resolve().parents:
        raise ValueError('Public summary must be outside the private output directory')
    evidence = [args.baseline, *args.sessions, *args.candidate_sessions, *args.evidence_files,
                Path(__file__)] + ([args.previous_csv] if args.previous_csv else []) + (
                [args.comparison_workbook] if args.comparison_workbook else [])
    initial_hashes = {p.resolve(): digest(p) for p in evidence}
    output_names = ['manifest.json', 'trial_metrics.json', 'candidate_trial_metrics.json',
                    'previous_replay_deltas.json', 'workbook_detail_deltas.json',
                    'session_action_aggregates.json']
    if any(p.resolve() in initial_hashes for p in [args.summary, *[
            args.private_dir/name for name in output_names]]):
        raise ValueError('An output would overwrite an input')
    data = read_json(args.baseline)
    baseline = {}
    for name, value in data.items():
        w, h = value['video_info']['width'], value['video_info']['height']
        coords = [[[f['landmarks_px'][n]['x']/w, f['landmarks_px'][n]['y']/h] for n in NAMES]
                  for f in value['frames'] if f['detected']]
        baseline[name.split('_')[0]] = preprocess(coords)
    rows, inputs, counts = load_cohort(args.sessions, baseline)
    candidate_rows, candidate_inputs, candidate_counts = (load_cohort(args.candidate_sessions, baseline)
        if args.candidate_sessions else ([], [], {}))
    summary = dict(status='partial_reconciliation_historical_body_scores_unresolved',
                   weights=WEIGHTS, rounded_maxima=MAXIMA,
                   tolerances=dict(floating_absolute=FLOAT_ATOL, three_decimal_display_absolute=DISPLAY_ATOL),
                   historical_code_cohort=cohort_summary(rows, counts),
                   displayed_table7_weighted_sums={str(lv): weighted(m) for lv, m in TABLE7.items()},
                   displayed_body_level_mean=float(np.mean([.528, .546, .493])))
    if candidate_rows:
        summary['downloads_candidates_after_exact_trial_payload_deduplication'] = cohort_summary(candidate_rows, candidate_counts)
    checks = {}
    checks['linear_aggregation'] = all(abs(value['mean_weighted_minus_weighted_mean']) <= FLOAT_ATOL
        for level in summary['historical_code_cohort']['levels'].values()
        for value in level.values())
    table_deltas = {str(lv): {m: summary['historical_code_cohort']['levels'][str(lv)]
        ['table7_candidate_21']['metric_means'][m]-TABLE7[lv][m] for m in MAXIMA} for lv in (1, 2, 3)}
    summary['table7_recomputed_minus_displayed'] = table_deltas
    checks['all_nine_composite_table7_values_round_to_display'] = all(abs(delta[m]) <= DISPLAY_ATOL
        for delta in table_deltas.values() for m in WEIGHTS)
    summary['table7_other_metric_diagnostic'] = dict(
        matched_display_count=sum(abs(d) <= DISPLAY_ATOL for delta in table_deltas.values() for d in delta.values()),
        total_values=21,
        all_21_within_display_tolerance=all(abs(d) <= DISPLAY_ATOL
            for delta in table_deltas.values() for d in delta.values()))
    checks['session_and_trial_equal_means_agree_for_balanced_design'] = all(
        abs(summary['historical_code_cohort']['levels'][str(lv)][p]['trial_equal_score']-
            summary['historical_code_cohort']['levels'][str(lv)][p]['session_equal_score']) <= FLOAT_ATOL
        for lv in (1, 2, 3) for p in ('verified_final_15', 'grid_definition_21'))
    comparison_rows = []
    if args.previous_csv:
        summary['previous_replay_comparison'], comparison_rows = compare_previous(rows, args.previous_csv)
        checks['previous_replay_three_composite_terms_and_score_match'] = all(
            v <= FLOAT_ATOL for k, v in summary['previous_replay_comparison']['max_abs_delta'].items()
            if k == 'score' or any(k.endswith('_'+m) for m in WEIGHTS))
    workbook_comparisons = []
    if args.comparison_workbook:
        summary['comparison_workbook'], workbook_comparisons = inspect_workbook(rows, args.comparison_workbook)
        checks['workbook_12_details_match_21_pair_definition_at_display_precision'] = (
            summary['comparison_workbook']['human_detail_rows'] == 12 and
            summary['comparison_workbook']['detail_comparisons'][1]['all_within_display_tolerance'])
    # Counterfactual: vary one evidenced definition at a time on identical rows.
    summary['level3_definition_bridge'] = {
        'trial15_clipped_dr_recorded': summarize([r for r in rows if r['level'] == 3], 15)['trial_equal_score'],
        'trial21_clipped_dr_recorded': summarize([r for r in rows if r['level'] == 3], 21)['trial_equal_score'],
        'trial21_unclipped_dr_recorded': trial21_unclipped([r for r in rows if r['level'] == 3]),
        'trial21_unclipped_dr_one': trial21_unclipped([r for r in rows if r['level'] == 3], False),
        'six_action_raw_mean21_unclipped_dr_one': table7_path([r for r in rows if r['level'] == 3])['score'],
        'six_action_raw_mean15_unclipped_dr_one': table7_path([r for r in rows if r['level'] == 3], 15)['score'],
        'displayed_table7_arithmetic': weighted(TABLE7[3]),
    }
    summary['checks'] = checks
    if not all(checks.values()):
        raise ValueError('Required reconciliation check failed: '+str(checks))
    checks['input_and_code_hashes_unchanged_during_run'] = all(digest(p) == initial_hashes[p.resolve()]
                                                            for p in evidence)
    if not checks['input_and_code_hashes_unchanged_during_run']:
        raise ValueError('Input or code changed while the replay was running')
    summary['reported_value_assessment'] = {
        '0.528': dict(target='body_level_1', status='not_reproduced_by_inspected_definitions'),
        '0.546': dict(target='body_level_2', status='not_reproduced_by_inspected_definitions'),
        '0.493': dict(target='body_level_3', status='not_reproduced_by_inspected_definitions'),
        '0.522': dict(target='body_overall', status='rounded_body_level_mean_only_not_raw_reproduction'),
        '0.557': dict(target='table10_level_3', status='table7_candidate_and_displayed_arithmetic_compatible_historical_run_unconfirmed'),
    }
    manifest = dict(runtime=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__),
                    files=[dict(path=str(p.resolve()), sha256=digest(p)) for p in evidence],
                    inputs=inputs, candidate_inputs=candidate_inputs,
                    maxima_origin='rounded constants in archived scripts; dynamic maxima not regenerated',
                    saved_metric_comparison='not available: original trial JSON has coordinates and counts only')
    write_json(args.private_dir/'manifest.json', manifest)
    write_json(args.private_dir/'trial_metrics.json', rows)
    write_json(args.private_dir/'candidate_trial_metrics.json', candidate_rows)
    write_json(args.private_dir/'previous_replay_deltas.json', comparison_rows)
    write_json(args.private_dir/'workbook_detail_deltas.json', workbook_comparisons)
    private_groups = {}
    for field in ('session', 'action'):
        private_groups[field] = {key: {str(lv): summarize(
            [r for r in rows if r[field] == key and r['level'] == lv], 15) for lv in (1, 2, 3)}
            for key in sorted(set(r[field] for r in rows))}
    write_json(args.private_dir/'session_action_aggregates.json', private_groups)
    write_json(args.summary, summary)
    print(json.dumps(dict(status=summary['status'], cohort_counts=counts, checks=checks), indent=2))


if __name__ == '__main__':
    main()
