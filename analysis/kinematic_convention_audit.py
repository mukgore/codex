"""Controlled FK convention comparison; not a fitted hand/clinical mapping."""
import argparse
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

from validation_v03.session_artifacts import canonical,_private


def run(worker_root,output):
    output=_private(output)
    if output.exists():raise FileExistsError('New private controlled reference run required')
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    from experiments.motion_fixture.kinematic_conventions import (
        VERSION,chain,equivalent_modified_inputs,isolated_mcp_vector,ISOLATED_BMC_BASIS,
    )
    from experiments.motion_fixture.biomechanical_features import signed_angles,rotation
    output.mkdir(parents=True);chains=[];vectors=[]
    grids={'nonthumb':list(product((-.2,0.,.2),(-.25,0.,.25),(0.,.35,.7),(0.,.4),(0.,.3))),
           'thumb':list(product((-.3,0.,.3),(0.,.4),(0.,.5),(0.,.5)))}
    lengths={'nonthumb':np.array([1.,.75,.55,.4]),'thumb':np.array([1.,.8,.6])}
    for kind,grid in grids.items():
        for scale in (1.,1.7):
            for q in grid:
                a=chain(kind,q,lengths[kind]*scale,'BIO07_standard_DH')
                modified,alignment=equivalent_modified_inputs(kind,q)
                b=chain(kind,modified,lengths[kind]*scale,'BIO06_modified_DH')
                aligned=b['points']@alignment[:3,:3].T
                point_error=float(np.abs(a['points']-aligned).max())
                transform_error=float(np.abs(a['tip_transform']-alignment@b['tip_transform']).max())
                naive=chain(kind,q,lengths[kind]*scale,'BIO06_modified_DH')
                naive_error=float(np.abs(a['points']-naive['points']).max())
                if max(point_error,transform_error)>1e-12:raise ValueError('Declared source-chain correspondence failed')
                chains.append({'kind':kind,'scale':scale,'standard_angles_radians':list(q),
                    'modified_angles_radians':modified.tolist(),'max_point_error':point_error,
                    'max_tip_transform_error':transform_error,'naive_same_inputs_point_error':naive_error})
    for abduction,flexion in product((-.4,-.2,0.,.2,.4),(-.9,-.45,0.,.45,.9)):
        vector=isolated_mcp_vector(abduction,flexion)
        pair=signed_angles(ISOLATED_BMC_BASIS.T@vector)
        reconstruction=ISOLATED_BMC_BASIS@rotation(*pair)@np.array([0.,0.,1.])
        error=float(np.abs(reconstruction-vector).max())
        if error>1e-12:raise ValueError('Chosen-basis BMC vector reconstruction failed')
        vectors.append({'dh_abduction_radians':abduction,'dh_flexion_radians':flexion,
            'bmc_pair_radians':pair.tolist(),'vector_error':error,
            'naive_angle_pair_max_difference_radians':float(np.abs(pair-[flexion,abduction]).max())})
    (output/'chain_cases.private.json').write_bytes(canonical(chains))
    (output/'isolated_mcp_cases.private.json').write_bytes(canonical(vectors))
    summary={'scope':'published_local_chain_convention_and_chosen_basis_vector_reference_only',
        'version':VERSION,'chain_cases_n':len(chains),'nonthumb_cases_n':sum(r['kind']=='nonthumb' for r in chains),
        'thumb_cases_n':sum(r['kind']=='thumb' for r in chains),
        'max_aligned_point_error':max(r['max_point_error'] for r in chains),
        'max_aligned_tip_transform_error':max(r['max_tip_transform_error'] for r in chains),
        'naive_same_inputs_mismatch_cases_n':sum(r['naive_same_inputs_point_error']>1e-12 for r in chains),
        'isolated_mcp_vector_cases_n':len(vectors),'max_bmc_vector_reconstruction_error':max(r['vector_error'] for r in vectors),
        'max_naive_bmc_dh_angle_difference_radians':max(r['naive_angle_pair_max_difference_radians'] for r in vectors),
        'length_unit':'engineering_reference_units','source_tables':['BIO-07 Tables I-II','BIO-06 Tables 7-8'],
        'nonthumb_declared_correspondence':'negate modified-DH MCP abduction input and apply output Rx(-pi/2)',
        'thumb_declared_correspondence':'same joint inputs with explicit modified-DH terminal tip translation',
        'new_model_inference':False,'mano_rig_mapping_verified':False,'clinical_neutral_axes_verified':False,
        'biological_validity_proven':False,'numeric_profile_changed':False,'release_allowed':False,
        'limitations':['Two local mathematical chain conventions only; full hand wrist/finger offsets and anthropometry are not fitted.',
            'BMC isolated neutral basis is explicitly authored, not measured from a participant or MANO anatomy.',
            'Same endpoint direction does not uniquely determine axial twist or certify a downstream clinical joint frame.',
            'Engineering angle grid/lengths are not admissible physiological limits; original source table conflicts remain unresolved.']}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();print(json.dumps(run(a.worker_root,a.output)))
