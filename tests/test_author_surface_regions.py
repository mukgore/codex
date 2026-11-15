import unittest
import numpy as np

from analysis.runtime_benchmark.author_surface_regions import (
    FINGER_LINKS,review_neutral,whole_region_faces,protective_union,undirected_topology_equal,
)


def sample():
    joints=np.zeros((21,3))
    for f,b in enumerate((1,5,9,13,17)):
        for j in range(4): joints[b+j]=[f*10.,2.+j,0.]
    vertices=np.array([(joints[a]+joints[b])/2 for a,b in FINGER_LINKS]+[[20.,1.,0.],[20.,0.,0.]])
    vertices[:,2]=.01
    return np.arange(17),vertices,joints,np.array([[0,3,6],[6,7,8],[7,9,10],[15,16,12]])


class AuthorSurfaceRegionTests(unittest.TestCase):
    def test_expected_model_region_geometry_and_reflected_hand_are_distinguished_from_clinical_proof(self):
        labels,v,j,f=sample()
        for matrix in (np.eye(3),np.diag([-1.,1.,1.])):
            row=review_neutral(labels,v@matrix,j@matrix,f)
            self.assertEqual(row['finger_centroids_matching_expected_links_n'],15)
            self.assertFalse(row['clinical_or_independent_anatomical_annotation'])
        labels=labels.copy();labels[[6,9]]=labels[[9,6]]
        self.assertEqual(review_neutral(labels,v,j,f)['finger_centroids_matching_expected_links_n'],13)

    def test_whole_face_selection_and_union_never_shrink_previous_protection(self):
        labels,v,j,f=sample();selected=whole_region_faces(labels,f,[6,7])
        np.testing.assert_array_equal(selected,[0,1,2])
        np.testing.assert_array_equal(protective_union(np.array([3]),selected,len(f)),[0,1,2,3])
        with self.assertRaises(ValueError):protective_union(np.array([4]),selected,len(f))

    def test_connectivity_comparison_allows_winding_and_face_order_but_not_index_changes(self):
        _,_,_,f=sample()
        self.assertTrue(undirected_topology_equal(f,f[::-1,::-1]))
        changed=f.copy();changed[0,0]=2
        self.assertFalse(undirected_topology_equal(f,changed))

    def test_missing_region_noninteger_labels_and_degenerate_bones_fail_closed(self):
        labels,v,j,f=sample()
        for bad in (labels.astype(float),np.zeros(17,dtype=int)):
            with self.assertRaises(ValueError):review_neutral(bad,v,j,f)
        j[2]=j[1]
        with self.assertRaises(ValueError):review_neutral(labels,v,j,f)
        with self.assertRaises(ValueError):whole_region_faces(labels,f,[17])


if __name__=='__main__':unittest.main()
