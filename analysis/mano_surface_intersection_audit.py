"""Recorded sampled-surface diagnostic on private random MANO arrays."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import numpy as np

from validation_v03.execution_record import verify
from validation_v03.session_artifacts import canonical,decode,_read,_private


def run(source,source_record,worker_root,output):
    source=Path(source).resolve(strict=True);output=_private(output)
    if output.exists():raise FileExistsError('New private diagnostic root required')
    before=verify(source_record);receipt=decode(_read(Path(source_record)/'receipt.private.json'))
    if before['state']!='EXITED_ZERO' or [Path(r).resolve() for r in receipt['artifact_roots']]!=[source]:
        raise ValueError('Completed recorded source root required')
    inputs=sorted(source.glob('*/native_output.private.npz'))
    if len(inputs)!=8:raise ValueError('Explicit eight-case source contract required')
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    from experiments.motion_fixture.mesh_intersections import VERSION,RELATIVE_EPSILON,topology,frame
    output.mkdir(parents=True);rows=[]
    for index,path in enumerate(inputs):
        with np.load(path,allow_pickle=False) as data:
            vertices=data['vertices'];faces=data['faces'];times=data['times_seconds']
            if vertices.shape!=(24,778,3) or faces.shape!=(1538,3) or times.shape!=(24,) or (np.diff(times)<=0).any():
                raise ValueError('Full native mesh and complete sampled time contract required')
            mesh=topology(faces,778);results=[]
            for number,points in enumerate(vertices):
                result=frame(points,mesh)
                results.append({'frame_idx':number,'time_seconds':float(times[number]),**result})
        row={'case':path.parent.name,'frames_n':len(results),
            'unmeasurable_frames_n':sum(r['state']=='UNMEASURABLE_DEGENERATE_TRIANGLES' for r in results),
            'indicator_frames_n':sum(r['state']=='SURFACE_INTERSECTION_INDICATORS' for r in results),
            'two_plane_straddling_frames_n':sum(bool(r['pair_ids'].get('two_plane_straddling_indicator')) for r in results),
            'coplanar_overlap_frames_n':sum(bool(r['pair_ids'].get('coplanar_overlap')) for r in results),
            'touch_or_ambiguous_frames_n':sum(bool(r['pair_ids'].get('touch_or_numerically_ambiguous')) for r in results),
            'tested_pair_instances_n':sum(r['tested_pairs_n'] for r in results),
            'boundary_edges_n':mesh['boundary_edges_n'],'nonmanifold_edges_n':mesh['nonmanifold_edges_n'],
            'shared_vertex_pairs_excluded_per_frame_n':mesh['shared_vertex_pairs_excluded_n']}
        (output/(path.parent.name+'.surface.private.json')).write_bytes(canonical({'summary':row,'frames':results}))
        rows.append(row);print('Mesh cases completed: '+str(index+1)+'/8',flush=True)
    if verify(source_record)!=before:raise ValueError('Source execution evidence changed during inspection')
    summary={'scope':'recorded_sampled_non_shared_vertex_triangle_surface_diagnostic',
        'algorithm_version':VERSION,'reference':'GEO-01 Eberly separating axes Sec.9; independent implementation',
        'relative_numeric_epsilon':RELATIVE_EPSILON,'cases_n':len(rows),'frames_n':sum(r['frames_n'] for r in rows),
        **{key:sum(r[key] for r in rows) for key in ('unmeasurable_frames_n','indicator_frames_n',
            'two_plane_straddling_frames_n','coplanar_overlap_frames_n','touch_or_ambiguous_frames_n','tested_pair_instances_n')},
        'indicator_cases_n':sum(r['indicator_frames_n']>0 for r in rows),
        'boundary_edge_counts':dict(Counter(str(r['boundary_edges_n']) for r in rows)),
        'nonmanifold_edge_counts':dict(Counter(str(r['nonmanifold_edges_n']) for r in rows)),
        'cases':rows,'new_model_inference':False,'biological_validity_proven':False,
        'continuous_collision_free_proven':False,'volume_penetration_free_proven':False,
        'original_quarantine_preserved':True,'release_allowed':False,
        'limitations':['Shared-vertex face pairs excluded and counted; overlap away from the common vertex can be missed.',
            'Finite precision tolerance and sampled instants only; no exact predicates or continuous collision.',
            'Surface contacts/plane straddling are indicators, not penetration volume/depth or force measurements.',
            'Closed-surface containment, anatomical correspondence, hand-object physics and human comfort unchecked.',
            'Original failed biological admission remains unchanged; no source mutation or pool promotion.']}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','source-record','worker-root','output'):parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();print(json.dumps(run(a.source,a.source_record,a.worker_root,a.output)))
