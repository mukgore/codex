"""Review model region correspondence; never infer clinical/anatomical approval."""
import numpy as np

FINGER_LINKS = tuple((b+j,b+j+1) for b in (1,5,9,13,17) for j in range(3))


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
