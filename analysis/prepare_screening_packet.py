"""Create private planning records, never participant observations or consent signatures."""
import argparse
import json
from pathlib import Path
import random


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    out = args.output.resolve()
    if (out.exists() or 'private_artifacts' not in out.parts
            or any((parent / '.git').exists() for parent in out.parents)):
        p.error('Choose a new private_artifacts directory outside repositories')
    out.mkdir(parents=True)
    families = {'A01': 'F01', 'A02': 'F02', 'A03': 'F02', 'A04': 'F03',
                'A05': 'F03', 'A06': 'F04', 'A07': 'F04'}
    jobs = []
    for motion, family in families.items():
        for take in range(1, 4):
            jobs.append({'capture_id': f'{motion}_T{take:02}', 'motion_id': motion,
                         'family_id': family, 'take': take, 'status': 'AWAITING_CAPTURE',
                         'source_path': None, 'source_sha256': None,
                         'intended_duration_seconds': 8,
                         'performer_id': None, 'actual_pts_path': None,
                         'consent_record_id': None, 'qc_result': None,
                         'failure_reason': None})
    rights = {'version': 'rights-20261110-v1',
              'evidence': [{'date': '2026-11-10', 'type': 'user_chat_self_declaration',
                            'statement': 'Existing videos were filmed by user and show user hand.'},
                           {'date': '2026-11-10', 'type': 'user_chat_instruction',
                            'statement': 'Keep private permanently.'}],
              'scope': 'existing self-captured hand videos discussed in stimulus intake',
              'ownership_basis': 'SELF_DECLARED_NOT_INDEPENDENTLY_VERIFIED',
              'research_analysis': 'ALLOWED_BY_CURRENT_TASK',
              'occlusion_and_coordinate_derivatives': 'ALLOWED_BY_CURRENT_TASK',
              'retention': 'INDEFINITE_PRIVATE_NO_SCHEDULED_DELETION',
              'public_delivery': 'NOT_AUTHORIZED', 'commercial_use': 'NOT_AUTHORIZED',
              'external_service_upload': 'NOT_AUTHORIZED',
              'release_allowed': False,
              'independent_holdout': False,
              'third_party_participant_consent': 'NOT_OBTAINED',
              'access': 'user and task-authorized local processing; no additional people designated'}
    # Slots are plans, not enrolled participants. Each slot sees a family only once.
    rng = random.Random(20261110)
    slots = []
    for group, condition in enumerate(['unmasked', 'black', 'skin']):
        for index in range(12):
            motions = ['A01', 'A02' if index % 2 == 0 else 'A03',
                       'A04' if (index // 2) % 2 == 0 else 'A05',
                       'A06' if (index // 3) % 2 == 0 else 'A07']
            rng.shuffle(motions)
            slots.append({'slot_id': f'SLOT_{group * 12 + index + 1:02}',
                          'status': 'UNFILLED_PLAN', 'participant_id': None,
                          'condition': condition, 'consent_record_id': None,
                          'prior_exposure': None, 'experience_stratum': None,
                          'trials': [{'order': i + 1, 'motion_id': motion,
                                      'family_id': families[motion],
                                      'stimulus_version': None, 'outcome': None}
                                     for i, motion in enumerate(motions)]})
    for slot in slots:
        assert len({t['family_id'] for t in slot['trials']}) == 4
    counts = {}
    for slot in slots:
        for trial in slot['trials']:
            key = f"{slot['condition']}/{trial['motion_id']}"
            counts[key] = counts.get(key, 0) + 1
    assert all(n == (12 if key.endswith('/A01') else 6) for key, n in counts.items())
    records = {'rights.private.json': rights, 'capture_jobs.private.json': jobs,
               'allocation_plan.private.json': {'status': 'DRAFT_NOT_ENROLLED',
                                                'planned_slots': 36,
                                                'planned_trials': 144,
                                                'cell_counts': counts, 'slots': slots},
               'response_template.private.json': {
                   'trial_id': None, 'participant_id': None, 'stimulus_id': None,
                   'protocol_version': None, 'assigned_condition': None,
                   'family_id': None, 'free_response_before_options': None,
                   'finger': None, 'contact': None, 'order': None, 'count': None,
                   'flexion_range': None, 'peak_time_seconds': None,
                   'confidence_1_to_5': None, 'cannot_judge': None,
                   'response_after_options': None, 'technical_error': None,
                   'aborted': None, 'rater_1': None, 'rater_2': None,
                   'adjudication': None, 'categorical_complete_correct': None}}
    for filename, data in records.items():
        (out / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                                   encoding='utf-8')
    print(json.dumps({'capture_jobs': len(jobs), 'planned_slots': len(slots),
                      'planned_trials': 144, 'family_duplicates_per_slot': 0,
                      'cell_balance_verified': True, 'actual_observations': 0}))


if __name__ == '__main__':
    main()
