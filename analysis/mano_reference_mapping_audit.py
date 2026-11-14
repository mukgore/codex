"""Read-only saved MANO reference audit; no model imports/inference or SI guess."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import zipfile

from analysis.runtime_benchmark.journal import verify_bundle
from validation_v03.run_manifest import read,snapshot_file
from validation_v03.session_artifacts import canonical,decode,_private,_read


def execute(mean_root,flat_root,worker_root,tip_source,worker_candidate,source_provenance,source_postflight,output):
    output=_private(output)
    if output.exists():raise FileExistsError('Preserve prior mapping audits')
    roots=[Path(p).resolve(strict=True) for p in (mean_root,flat_root)]
    worker_root=Path(worker_root).resolve(strict=True);tip_source=Path(tip_source).resolve(strict=True)
    source_provenance=_private(source_provenance);source_postflight=Path(source_postflight).resolve(strict=True)
    old,old_fingerprint=read(source_provenance);post=decode(_read(source_postflight))
    if post['status']!='CURRENT_SNAPSHOT_MATCHES' or post['manifest_sha256']!=old_fingerprint:
        raise ValueError('Saved prior postflight is not linked to the original snapshot')
    for row in old['inputs']:
        current=snapshot_file(row['path'])
        if any(current[k]!=row[k] for k in ('bytes','sha256')):raise ValueError('Prior recorded input bytes changed')
    old_bound={Path(row['path']).resolve() for row in old['inputs']}
    tip_fingerprint=snapshot_file(tip_source);candidate=Path(worker_candidate).resolve(strict=True)
    candidate_bytes=candidate.read_bytes();lf=candidate_bytes.replace(b'\r\n',b'\n')
    candidate_variants={hashlib.sha256(v).hexdigest() for v in (candidate_bytes,lf,lf.replace(b'\n',b'\r\n'))}
    sys.path.insert(0,str(worker_root))
    from experiments.motion_fixture.mano_reference_audit import audit,named_tip_ids
    tips=named_tip_ids(tip_source)
    expected={hand+'_pc'+str(i) for hand in ('left','right') for i in range(3)}
    output.mkdir(parents=True,exist_ok=False);cases=[]
    for label,root in zip(('legacy_default_label','explicit_flat_mean_label'),roots):
        if {p.name for p in root.iterdir() if p.is_dir()}!=expected:raise ValueError('Expected six-case source layout required')
        for case in sorted(expected):
            folder=root/case;pilot=folder/'supervised/worker_journal'
            files=[pilot/n for n in ('mano_report.json','private_reference.json','private_surface.npz','authored_source.avi')]
            if not set(files).issubset(old_bound):raise ValueError('Pilot source was not bound by the prior reviewed snapshot')
            bundle=folder/'worker_bundle.zip';recovered=verify_bundle(bundle)
            if recovered['status']!='COMPLETED' or recovered['completed_frames']!=24:
                raise ValueError('Actual stored worker journal is not a completed 24-frame run')
            with zipfile.ZipFile(bundle) as archive:
                if archive.read('manifest.json')!=(pilot/'manifest.json').read_bytes() or archive.read('events.jsonl')!=(pilot/'events.jsonl').read_bytes():
                    raise ValueError('Worker bundle differs from local journal files')
            manifest=decode(_read(pilot/'manifest.json'));report=decode(_read(pilot/'mano_report.json'))
            if report['hand']+'_'+'pc'+str(report['component'])!=case:raise ValueError('Source case label conflicts with stored metadata')
            result=audit(pilot,tips)
            row={'input_set_label':label,'case':case,'journal_completed_frames':recovered['completed_frames'],
                 'candidate_worker_source_matches_recorded_bytes':manifest.get('worker_source_sha256') in candidate_variants,
                 'flat_mean_flag_recorded_in_report':'flat_hand_mean' in report,**result}
            (output/(label+'_'+case+'.private.json')).write_bytes(canonical(row));cases.append(row)
    for row in old['inputs']:
        actual=snapshot_file(row['path'])
        if any(actual[k]!=row[k] for k in ('bytes','sha256')):raise ValueError('Prior source changed during mapping audit')
    if snapshot_file(tip_source)!=tip_fingerprint or candidate.read_bytes()!=candidate_bytes or read(source_provenance)[1]!=old_fingerprint:
        raise ValueError('Mapping source or provenance changed during analysis')
    if any(name in sys.modules for name in ('torch','smplx')):raise ValueError('This audit must not import model runtime')
    groups={}
    for label in sorted({r['input_set_label'] for r in cases}):
        rows=[r for r in cases if r['input_set_label']==label];spans=[r['bone_relative_spans'] for r in rows if r['bone_relative_spans'] is not None]
        groups[label]={'cases_n':len(rows),'frames_n':sum(r['frames_n'] for r in rows),
            'all_named_tips_match_cases_n':sum(r['tip_mapping_all_five_match'] for r in rows),
            'projection_matches_cases_n':sum(r['projection_matches_declared_framing'] for r in rows),
            'reference_quarantined_cases_n':sum(r['state']=='QUARANTINED_REFERENCE_CONSISTENCY' for r in rows),
            'measurable_feature_frames_n':sum(r['measurable_feature_frames_n'] for r in rows),
            'feature_geometry_error_counts':dict(Counter(e['code'] for r in rows for e in r['geometry_errors'])),
            'flat_mean_flag_recorded_cases_n':sum(r['flat_mean_flag_recorded_in_report'] for r in rows),
            'current_candidate_worker_source_matches_cases_n':sum(r['candidate_worker_source_matches_recorded_bytes'] for r in rows),
            'max_projection_abs_error_px':max(r['projection_max_abs_error_px'] for r in rows),
            'max_non_tip_joint_edge_relative_span':max((s['non_tip_joint_edges_max_relative_span'] for s in spans),default=None),
            'max_surface_tip_edge_relative_span':max((s['surface_tip_edges_max_relative_span'] for s in spans),default=None)}
    summary={'scope':'stored_mano_reference_mapping_and_native_unit_evidence_only',
        'prior_input_files_checked_before_and_after_n':len(old['inputs']),
        'source_cases_n':len(cases),'source_frames_n':sum(r['frames_n'] for r in cases),
        'worker_journal_completed_cases_n':len(cases),'groups':groups,'physical_unit_verified_cases_n':0,
        'non_tip_joint_semantics_independently_recovered':False,
        'length_unit_policy':'model_native_units_only_no_inferred_meter_or_mm_conversion',
        'biological_validity_proven':False,'full_generator_ready':False,'release_allowed':False,
        'models_imported':False,'new_model_inference':False,'new_human_observations_n':0,
        'limitations':['Names/hand/mean flags remain recorded declarations, with only the stated saved-geometry relations checked.',
            'Current candidate worker-source mismatch is not proof that no historical source exists elsewhere.',
            'Named surface tips are not rigid anatomical joint centers; authored fixed-20-bone policy is not applied.',
            'No physical unit, whole-joint semantic recovery, admissible motion limits, collision/physics or human validation.']}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('mean-root','flat-root','worker-root','tip-source','worker-candidate','source-provenance','source-postflight','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();print(json.dumps(execute(a.mean_root,a.flat_root,a.worker_root,a.tip_source,a.worker_candidate,a.source_provenance,a.source_postflight,a.output)))
