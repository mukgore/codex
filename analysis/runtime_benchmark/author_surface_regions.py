"""Review model region correspondence; never infer clinical/anatomical approval."""
import ast
import hashlib
import json
from pathlib import Path

import numpy as np

FINGER_LINKS = tuple((b+j,b+j+1) for b in (1,5,9,13,17) for j in range(3))
PROTECTION_MODES = ('author_region_union','legacy_rest_proxy')


def blob(path):
    data=Path(path).read_bytes()
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def validate_protection_request(mode,profile,assignment,review):
    if mode not in PROTECTION_MODES:raise ValueError('Explicit registered protection mode required')
    values=(profile,assignment,review)
    if mode=='author_region_union' and any(v is None for v in values):
        raise ValueError('Author-region union requires pinned profile, assignment and source-review files; no legacy fallback')
    if mode=='legacy_rest_proxy' and any(v is not None for v in values):
        raise ValueError('Legacy reproduction must not silently ignore author-region inputs')


def source_profile(profile,assignment,review):
    profile=json.loads(Path(profile).read_text());review=Path(review).resolve(strict=True)
    if (profile['version']!='cpf_paper_palette_geometry_region_review_v1'
            or profile['release_allowed'] is not False or profile['review_target_region_ids']!=[6,7]
            or blob(assignment)!=profile['assignment_blob_sha']
            or blob(review/'cpf_viz_utils.py')!=profile['author_palette_blob_sha']
            or blob(review/'author_manolayer.py')!='0e96fe330efee46ed898e4211896a50db2f05eba'):
        raise ValueError('Pinned source blobs and explicit review-only region profile required')
    # Parse literal RGB assignments without importing/executing author code.
    tree=ast.parse((review/'cpf_viz_utils.py').read_text());colors={}
    for node in ast.walk(tree):
        if not isinstance(node,ast.Assign) or len(node.targets)!=1:continue
        target=node.targets[0];value=node.value
        if not (isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and target.value.id=='vertex_color'
                and isinstance(target.slice,ast.Compare) and isinstance(target.slice.left,ast.Name) and target.slice.left.id=='x'
                and len(target.slice.ops)==1 and isinstance(target.slice.ops[0],ast.Eq)
                and isinstance(target.slice.comparators[0],ast.Constant) and type(target.slice.comparators[0].value) is int
                and isinstance(value,ast.BinOp) and isinstance(value.op,ast.Div) and isinstance(value.left,ast.Call)
                and isinstance(value.left.func,ast.Attribute) and isinstance(value.left.func.value,ast.Name)
                and value.left.func.value.id=='np' and value.left.func.attr=='array'
                and isinstance(value.right,ast.Constant) and value.right.value==255.):continue
        colors[target.slice.comparators[0].value]=ast.literal_eval(value.left.args[0])
    if any(colors.get(r['id'])!=r['rgb'] for r in profile['regions']):
        raise ValueError('Project region colors do not match the pinned author palette')
    labels=np.loadtxt(assignment,dtype=int)
    if labels.shape!=(778,) or set(labels.tolist())!=set(range(17)):
        raise ValueError('Exact 778-vertex/17-region author assignment required')
    return profile,labels


def union_proxy(previous,labels,vertices,joints,faces):
    review=review_neutral(labels,vertices,joints,faces)
    if review['finger_centroids_matching_expected_links_n']!=15:
        raise ValueError('Current model region geometry does not match reviewed finger-link correspondence')
    selected=whole_region_faces(labels,faces,[6,7])
    original=np.asarray(previous['protected_face_ids']).copy()
    result=dict(previous)
    result.update(protected_face_ids=protective_union(original,selected,len(faces)),
                  original_rest_protected_face_ids=original,author_region_face_ids=selected,
                  author_finger_centroid_matches_n=15,
                  anatomical_coverage_proven=False,
                  definition='union of prior rest-nearest-bone whole faces and paper/palette-reviewed author middle proximal/intermediate whole faces')
    return result


def validated_arrays(labels, vertices, joints, faces):
    labels=np.asarray(labels);vertices=np.asarray(vertices,float);joints=np.asarray(joints,float);faces=np.asarray(faces)
    if (vertices.ndim!=2 or vertices.shape[1]!=3 or not np.isfinite(vertices).all()
            or joints.shape!=(21,3) or not np.isfinite(joints).all()
            or labels.shape!=(len(vertices),) or labels.dtype.kind not in 'iu'
            or set(np.unique(labels).tolist())!=set(range(17))
            or faces.ndim!=2 or faces.shape[1]!=3 or faces.dtype.kind not in 'iu'
            or not len(faces) or faces.min()<0 or faces.max()>=len(vertices)):
        raise ValueError('Finite matching native mesh/joints and all seventeen nonempty integer regions required')
    return labels,vertices,joints,faces


def segment_distances(points, joints):
    a=joints[[x for x,_ in FINGER_LINKS]];b=joints[[y for _,y in FINGER_LINKS]];d=b-a
    length2=np.sum(d*d,axis=1)
    if (length2<=1e-20).any(): raise ValueError('Nondegenerate declared finger links required')
    delta=points[:,None]-a
    t=np.clip(np.sum(delta*d,axis=2)/length2,0.,1.)
    return np.linalg.norm(delta-t[:,:,None]*d,axis=2)


def review_neutral(labels, vertices, joints, faces):
    labels,vertices,joints,faces=validated_arrays(labels,vertices,joints,faces)
    centroids=np.array([vertices[labels==i].mean(axis=0) for i in range(17)])
    center_distances=segment_distances(centroids,joints)
    owners=np.argmin(segment_distances(vertices,joints),axis=1)
    rows=[]
    for i in range(17):
        selected=labels==i
        rows.append({'region_id':i,'vertices_n':int(selected.sum()),
            'centroid_native':centroids[i].tolist(),
            'nearest_finger_link_index':int(np.argmin(center_distances[i])),
            'expected_link_index':i if i<15 else None,
            'centroid_nearest_expected_finger_link':bool(np.argmin(center_distances[i])==i) if i<15 else None,
            'vertex_nearest_expected_finger_link_fraction':float(np.mean(owners[selected]==i)) if i<15 else None})
    return {'regions':rows,'finger_centroids_matching_expected_links_n':sum(r['centroid_nearest_expected_finger_link'] is True for r in rows),
            'scope':'nearest finite finger-link geometric diagnostic; centroid agreement does not validate every region boundary',
            'clinical_or_independent_anatomical_annotation':False}


def whole_region_faces(labels, faces, region_ids):
    labels=np.asarray(labels);faces=np.asarray(faces)
    if (labels.ndim!=1 or labels.dtype.kind not in 'iu' or faces.ndim!=2 or faces.shape[1]!=3
            or faces.dtype.kind not in 'iu' or not len(faces) or faces.min()<0 or faces.max()>=len(labels)
            or not isinstance(region_ids,(tuple,list)) or not region_ids
            or any(type(i) is not int or i not in range(17) for i in region_ids)
            or any(not np.any(labels==i) for i in region_ids)):
        raise ValueError('Explicit present region IDs and compatible integer topology required')
    return np.flatnonzero(np.any(np.isin(labels[faces],region_ids),axis=1)).astype(np.int32)


def protective_union(existing, added, faces_n):
    arrays=[np.asarray(x) for x in (existing,added)]
    if (type(faces_n) is not int or faces_n<=0 or any(x.ndim!=1 or x.dtype.kind not in 'iu' or not len(x)
            or x.min()<0 or x.max()>=faces_n for x in arrays)):
        raise ValueError('Nonempty valid protected face lists required')
    return np.union1d(*arrays).astype(np.int32)


def undirected_topology_equal(a,b):
    a=np.asarray(a);b=np.asarray(b)
    if (a.ndim!=2 or a.shape[1]!=3 or a.shape!=b.shape or a.dtype.kind not in 'iu' or b.dtype.kind not in 'iu'):
        return False
    def ordered(x):
        x=np.sort(x,axis=1);return x[np.lexsort(x.T[::-1])]
    return bool(np.array_equal(ordered(a),ordered(b)))
