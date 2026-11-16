import unittest
import json
import numpy as np
from analysis.matched_display_analysis import exact_buckets,surface_weight_interval_for_static,serializable_lineage
from analysis.runtime_benchmark.common_camera_mask import WIDTH,HEIGHT


class MatchedAnalysisTests(unittest.TestCase):
    def test_same_payload_is_grouped_without_inventing_independent_file_names(self):
        groups=exact_buckets([('first',b'actual bytes'),('different-name',b'actual bytes'),('changed',b'actual byteS')])
        self.assertEqual(len(groups),2)
        self.assertEqual(groups[0]['members'],['first','different-name'])
        self.assertEqual(groups[1]['members'],['changed'])
        self.assertNotIn('payload',groups[0])

    def test_static_repetition_retains_surface_bound_and_rejects_exposed_union(self):
        xy=np.tile([256.,250.],(21,1));xy[0]=[256.,300.];xy[9]=[256.,200.]
        yy,xx=np.ogrid[:HEIGHT,:WIDTH]
        small=(xx-256)**2+(yy-250)**2<20**2
        legacy={'minimum_w3':.2,'maximum_w3':.8,'feasible':True}
        result=surface_weight_interval_for_static(legacy,xy,small)
        self.assertTrue(result['feasible']);self.assertEqual(len(result['surface_frame_minimum_w3']),25)
        self.assertEqual(len(set(result['surface_frame_minimum_w3'])),1)
        large=(xx-256)**2+(yy-250)**2<80**2
        self.assertFalse(surface_weight_interval_for_static(legacy,xy,large)['feasible'])

    def test_empty_union_or_invalid_geometry_never_qualifies_static_candidate(self):
        xy=np.tile([256.,250.],(21,1));xy[0]=[256.,300.];xy[9]=[256.,200.]
        target=np.zeros((HEIGHT,WIDTH),bool);legacy={'minimum_w3':.2,'maximum_w3':.8,'feasible':True}
        self.assertFalse(surface_weight_interval_for_static(legacy,xy,target)['feasible'])
        with self.assertRaises(ValueError):surface_weight_interval_for_static(legacy,np.full((21,2),np.nan),target)

    def test_lineage_serialization_preserves_findings_without_mutating_allocation_sets(self):
        report={'summary':{'declared_constraint_findings':{'MISSING_INDEPENDENT_PARTITIONS':1}},
          'private_findings':[{'code':'MISSING_INDEPENDENT_PARTITIONS'}],'allocations':[{'sources':{'one','two'}}]}
        result=serializable_lineage(report);decoded=json.loads(json.dumps(result))
        self.assertEqual(decoded['private_findings'],report['private_findings'])
        self.assertEqual(decoded['summary'],report['summary'])
        self.assertNotIn('allocations',result);self.assertEqual(report['allocations'][0]['sources'],{'one','two'})
