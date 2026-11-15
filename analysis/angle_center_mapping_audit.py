"""Label/feature regression on recorded MANO arrays; no clinical-axis approval."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

from validation_v03.execution_record import verify
from validation_v03.session_artifacts import canonical,decode,_read,_private


def run(source,source_record,literature,worker_root,output):
    source=Path(source).resolve(strict=True);output=_private(output)
    if output.exists():raise FileExistsError('New private mapping audit required')
    before=verify(source_record);receipt=decode(_read(Path(source_record)/'receipt.private.json'))
    if before['state']!='EXITED_ZERO' or [Path(p).resolve() for p in receipt['artifact_roots']]!=[source]:
        raise ValueError('Completed recorded source required')
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    from experiments.motion_fixture.biomechanical_features import extract,ANGLE_RECORDS,ANGLE_RECORD_VERSION
    literature=decode(_read(literature));rows=literature['table6_selected_rows']
    if literature['status']!='REFERENCE_EXTRACTION_NOT_ADMISSIBLE_PROFILE' or literature['production_profile_applied'] is not False:
        raise ValueError('Unapplied literature extraction required')
    finger_names={'THUMB':'thumb','INDEX':'index','MIDDLE':'middle','RING':'ring','PINKY':'little'}
    lookup={(finger_names[r['canonical_center_point'].split('_')[0]],r['candidate_clinical_joint']):r for r in ANGLE_RECORDS}
    selected=[]
    for row in rows:
        record=lookup[(row['finger'],row['joint'])]
        selected.append({'literature_source':'BIO-06','finger':row['finger'],'joint':row['joint'],**record,
            'status':'LABEL_CANDIDATE_ONLY_AXES_NEUTRAL_AND_SIGN_UNVERIFIED','numeric_limit_applied':False})
    output.mkdir(parents=True);checked_frames=0;checked_arrays=0;case_rows=[]
    files=sorted(source.glob('*/native_output.private.npz'))
    if len(files)!=8:raise ValueError('Eight recorded cases required')
    for path in files:
        spec=decode(_read(path.parent/'proposal.private.json'))
        original=decode(_read(path.parent/'assessment.private.json'))['private_features']
        with np.load(path,allow_pickle=False) as data:points=data['canonical_joints']
        if points.shape!=(24,21,3) or [r['frame_idx'] for r in original]!=list(range(24)):
            raise ValueError('Full ordered source and prior feature record required')
        for index,pose in enumerate(points):
            result=extract(pose,handedness=spec['hand'])
            for key,value in result.items():
                if isinstance(value,np.ndarray):
                    if not np.array_equal(value,np.asarray(original[index][key])):
                        raise ValueError('Numerical feature changed while clarifying center labels: '+key)
                    checked_arrays+=1
            checked_frames+=1
        case_rows.append({'case':path.parent.name,'frames_n':24,'numerical_feature_arrays_exactly_equal':True})
    if verify(source_record)!=before:raise ValueError('Source changed during mapping inspection')
    (output/'angle_records.private.json').write_bytes(canonical({'version':ANGLE_RECORD_VERSION,
        'records':list(ANGLE_RECORDS),'selected_literature_label_candidates':selected}))
    (output/'case_checks.private.json').write_bytes(canonical(case_rows))
    summary={'scope':'angle_center_child_label_clarification_and_saved_feature_regression',
        'angle_record_version':ANGLE_RECORD_VERSION,'cases_n':len(files),'frames_recomputed_n':checked_frames,
        'numerical_feature_arrays_exactly_equal_n':checked_arrays,'angle_centers_labeled_n':len(ANGLE_RECORDS),
        'selected_literature_label_candidates_n':len(selected),
        'verified_clinical_axis_mappings_n':0,'numeric_profile_changed':False,'new_model_inference':False,
        'biological_validity_proven':False,'release_allowed':False,
        'limitations':['Center/child is a canonical skeleton label correspondence, not independent anatomical annotation.',
            'BMC geometry frames and clinical/MDH neutral pose, rotation axes and signs remain unverified.',
            'Existing hand model quarantine and all unresolved rule limits remain unchanged.']}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','source-record','literature','worker-root','output'):parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();print(json.dumps(run(a.source,a.source_record,a.literature,a.worker_root,a.output)))
