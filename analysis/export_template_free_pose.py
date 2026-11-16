"""Export aggregate TF-02 measurements only; raw model/poses remain private."""
import argparse
import json
from pathlib import Path

from analysis.runtime_benchmark.mano_author_surface_audit import bound
from validation_v03.session_artifacts import canonical


def export(source, record):
    source, _, status = bound(source, record)
    data = json.loads((source/'summary.json').read_text())
    if data['native_forward_poses_n'] != 70 or len(data['cases']) != 64 or data['release_allowed'] is not False:
        raise ValueError('Complete quarantined preregistered pilot required')
    report = {k: data[k] for k in ('version', 'by_arm', 'representation_controls', 'native_forward_poses_n',
        'unique_experimental_proposals_n', 'nominal_arm_rows_n', 'U_reuses_B_geometry_and_measurements',
        'core_wall_ns', 'core_process_cpu_ns', 'journal_status', 'pending_BMC_state',
        'new_motion_sequences_n', 'new_videos_n', 'human_validity_proven',
        'new_independent_families_n', 'accepted_into_pool_n', 'release_allowed')}
    report['record_integrity'] = status['integrity']
    report['timing_scope'] = 'core setup/controls/proposal/SDK/QA/store and bound checks, excludes recorder snapshot and sealing; no video'
    report['by_hand_and_arm'] = []
    report['pose_timing_summary'] = []
    for hand in ('right', 'left'):
        for arm in ('A', 'B'):
            rows = [r for r in data['cases'] if r['hand'] == hand and r['arm'] == arm]
            report['by_hand_and_arm'].append({'hand': hand, 'arm': arm, 'proposals_n': len(rows),
                'model_surface_eligible_measured_n': sum(r['model_surface_eligible'] for r in rows),
                'model_excess_poses_n': sum(r['effective_model_excess_components_n'] > 0 for r in rows),
                'surface_indicator_poses_n': sum(r['surface_pairs_n'] > 0 for r in rows)})
    for arm in ('A', 'B'):
        rows = [r for r in data['cases'] if r['arm'] == arm]
        times = sorted(r['timing']['validated_pipeline_wall_ns'] for r in rows)
        report['pose_timing_summary'].append({'arm': arm, 'poses_n': len(rows),
            'wall_ns_min': times[0], 'wall_ns_median': (times[15]+times[16])/2,
            'wall_ns_max': times[-1], 'shared_model_setup_excluded': True,
            'video_generation': False})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('xb') as stream:
        stream.write(canonical(export(args.source, args.record)))
