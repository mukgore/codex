"""Actual feature/profile audit of owned fixtures, never an anatomy certificate."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
import sys

import numpy as np

from validation_v03.execution_record import verify
from validation_v03.run_manifest import read,snapshot_file
from validation_v03.session_artifacts import canonical,decode,_private,_read


def execute(source_root,worker_root,execution_record,profile_path,output):
    source_root=Path(source_root).resolve(strict=True);worker_root=Path(worker_root).resolve(strict=True)
    execution_record=_private(execution_record);output=_private(output);profile_path=Path(profile_path).resolve(strict=True)
    if output.exists():raise FileExistsError('Preserve previous biomechanics audits')
    before=verify(execution_record);receipt=decode(_read(execution_record/'receipt.private.json'))
    if before['mode']!='RECORDED_COMMAND_EXECUTION' or before['state']!='EXITED_ZERO' or receipt['artifact_roots']!=[str(source_root)]:
        raise ValueError('Existing completed surface execution must bind this source root')
    manifest,_=read(execution_record/'provenance')
    recorded={Path(row['path']).resolve():row for row in manifest['code_files']}
    for name in ('generate.py','grasp_contacts.py','contact.py'):
        path=worker_root/'experiments/motion_fixture'/name
        actual=snapshot_file(path);old=recorded.get(path.resolve())
        if old is None or any(actual[k]!=old[k] for k in ('bytes','sha256')):
            raise ValueError('Source recipe code differs from recorded source generation')
    sys.path.insert(0,str(worker_root))
    from dataset_pipeline.common import LANDMARK_NAMES
    from experiments.motion_fixture.generate import generate_motion,TEMPLATES
    from experiments.motion_fixture.grasp_contacts import KINDS,records,reflect_depth
    from experiments.motion_fixture.biomechanical_features import VERSION
    from experiments.motion_fixture.biomechanical_profile import validate,assess
    profile_bytes=_read(profile_path);profile=decode(profile_bytes);validate(profile)
    output.mkdir(parents=True,exist_ok=False)
    (output/'applied_profile.private.json').write_bytes(profile_bytes)
    cases=[];new_references=[];matched_frames=0
    def inspect_case(label,origin,frames):
        if [f['frame_idx'] for f in frames]!=list(range(len(frames))):raise ValueError('Complete ordered reference required')
        points=np.array([[[f['landmarks_world'][n][axis] for axis in ('x','y','z')] for n in LANDMARK_NAMES] for f in frames])
        times=[f['source_pts_ms']/1000 for f in frames]
        result=assess(points,times,profile,handedness='right',length_unit='authored_units')
        row={'case':label,'origin':origin,'handedness_scope':'authored canonical right declaration, not observed human',**result}
        (output/(label+'.assessment.private.json')).write_bytes(canonical(row));cases.append(row)
    for seed in (7,19):
        for kind in KINDS:
            original=records(kind,seed,24,12)
            controls={'source':original,'hand_reflection':reflect_depth(original,object_too=False),
                      'joint_reflection':reflect_depth(original,object_too=True)}
            for control,expected in controls.items():
                path=source_root/(kind+'_s'+str(seed))/control/'reference.private.json'
                actual=decode(_read(path))
                if actual!={'frames':expected,'source_info':{'width':512,'height':420,'fps':12,'total_frames':24}}:
                    raise ValueError('Stored reference does not match recorded procedural recipe')
                matched_frames+=len(expected)
                inspect_case(kind+'_s'+str(seed)+'_'+control,'existing_recorded_surface_reference',actual['frames'])
        for template in TEMPLATES:
            frames=generate_motion(template,seed,24,12)
            label=template+'_s'+str(seed)
            new_references.append({'case':label,'scope':'fresh_recomputation_of_existing_authored_template_not_human_data','frames':frames})
            inspect_case(label,'procedural_baseline_recomputation',frames)
    (output/'recomputed_templates.private.json').write_bytes(canonical(new_references))
    if _read(profile_path)!=profile_bytes or verify(execution_record)!=before:
        raise ValueError('Source evidence/profile changed during audit')
    groups={}
    for origin in sorted({row['origin'] for row in cases}):
        selected=[r for r in cases if r['origin']==origin]
        groups[origin]={'cases_n':len(selected),'frames_n':sum(r['frames_n'] for r in selected),
            'measurable_frames_n':sum(r['measurable_frames_n'] for r in selected),
            'states':dict(Counter(r['state'] for r in selected)),
            'geometry_error_counts':dict(Counter(e['code'] for r in selected for e in r['geometry_errors'])),
            'declared_rules_pass_cases_n':sum(r['declared_rules_pass'] for r in selected),
            'evidence_backed_rule_checks_pass_cases_n':sum(r['evidence_backed_rule_checks_pass'] for r in selected)}
    summary={'scope':'sampled_biomechanical_formula_mapping_and_pending_limits_diagnostic',
        'feature_version':VERSION,'profile_version':profile['profile_version'],'length_unit':profile['length_unit'],
        'source_execution_record_verified_before_and_after':True,'stored_reference_frames_recomputed_and_matched':matched_frames,
        'groups':groups,'total_cases_n':len(cases),'total_frames_n':sum(r['frames_n'] for r in cases),
        'unresolved_rules':sorted({k for r in cases for k in r['unresolved_rules']}),
        'biological_validity_proven':False,'full_generator_ready':False,'release_allowed':False,
        'new_human_observations_n':0,'learned_model_inference':False,
        'limitations':['Formula features are implemented; no accepted human/range-of-motion limits are bundled.',
            'Authored length units and thumb/rig anatomy correspondence remain unresolved.',
            'Unmeasurable palm bases are rejected, not silently repaired or certified as anatomical.',
            'No human comfort, anatomical mesh/self-collision, grasp dynamics or continuous-between-sample guarantee.']}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source-root','worker-root','execution-record','profile','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();print(json.dumps(execute(args.source_root,args.worker_root,args.execution_record,args.profile,args.output)))
