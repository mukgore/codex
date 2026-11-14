import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from analysis.runtime_benchmark.mano_recorded_producer import (
    ORDER, RAW_PARENTS, TIP_NAMES, authorize_inputs, camera, canonicalize, point_contract,
)
from validation_v03.run_manifest import snapshot_file


class RecordedProducerTests(unittest.TestCase):
    def setUp(self):
        self.vertices = np.arange(2*778*3, dtype=float).reshape(2,778,3)
        self.joints = np.arange(2*16*3, dtype=float).reshape(2,16,3)+10000
        self.tips = dict(zip(TIP_NAMES, (11,22,33,44,55)))

    def test_named_tips_and_native_joints_have_distinct_origins(self):
        result = canonicalize(self.vertices,self.joints,self.tips)
        for index,native in enumerate(ORDER):
            expected = self.joints[:,native] if native<16 else self.vertices[:,self.tips[TIP_NAMES[native-16]]]
            np.testing.assert_array_equal(result[:,index],expected)
        self.assertEqual(result.shape,(2,21,3))
        contract = point_contract([str(i) for i in range(21)],self.tips)
        points = contract['canonical_points']
        self.assertEqual(sorted(p['native_joint_index'] for p in points if p['point_kind']=='sdk_joint'),list(range(16)))
        self.assertEqual([p['mesh_vertex_index'] for p in points if p['point_kind']=='mesh_surface_tip'],list(self.tips.values()))
        self.assertEqual(contract['native_parent_contract'],list(RAW_PARENTS))
        self.assertFalse(contract['physical_SI_unit_verified'])
        self.assertFalse(contract['fixed_all_20_bone_policy_applicable'])

    def test_wrong_topology_nonfinite_and_duplicate_tips_rejected(self):
        with self.assertRaises(ValueError):canonicalize(self.vertices,np.zeros((2,21,3)),self.tips)
        bad=self.vertices.copy();bad[0,0,0]=np.nan
        with self.assertRaises(ValueError):canonicalize(bad,self.joints,self.tips)
        with self.assertRaises(ValueError):canonicalize(self.vertices,self.joints,{**self.tips,'thumb':22})

    def test_camera_fixed_basis_y_flip_and_scale(self):
        vertices=np.array([[[-1.,-1.,0.],[1.,1.,0.]]])
        joints=np.zeros((1,21,3));joints[0,9,1]=1;joints[0,17,0]=1
        projected,reference,depth,normal,meta=camera(vertices,joints)
        np.testing.assert_allclose(projected,[[[81.,385.],[431.,35.]]])
        np.testing.assert_allclose(reference[0,0],[256.,210.])
        np.testing.assert_allclose(depth,0);np.testing.assert_allclose(normal,[0,0,1])
        self.assertEqual(meta['pixels_per_model_native_unit'],175.)
        self.assertFalse(meta['physical_camera_calibrated'])
        with self.assertRaises(ValueError):camera(vertices,np.zeros_like(joints))

    def test_private_scope_and_original_inputs_remain_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);intake=root/'intake';models=intake/'models';models.mkdir(parents=True)
            files=[]
            for name in ('MANO_LEFT.pkl','MANO_RIGHT.pkl','LICENSE.txt','info.txt'):
                path=models/name;path.write_bytes(b'dummy fixture, never deserialize')
                files.append({'filename':name,**snapshot_file(path)})
            manifest=intake/'asset_manifest.json'
            manifest.write_text(json.dumps({'state':'FILES_STAGED_NOT_LOADED','release_allowed':False,
                'rights_status':'UNREVIEWED','files':files}))
            original=manifest.read_bytes();evidence=root/'prior.txt';evidence.write_text('fixture prior research instruction')
            scope={'purpose':'private_noncommercial_scientific_research','operating_or_commercial_clearance':False,
                'basis':'prior_user_provided_model_and_continuing_private_research_task',
                'intake_manifest_sha256':snapshot_file(manifest)['sha256'],
                'existing_session_evidence':[snapshot_file(evidence)]}
            record=root/'scope.json';record.write_text(json.dumps(scope))
            self.assertEqual(len(authorize_inputs(intake,record)),4)
            self.assertEqual(manifest.read_bytes(),original)
            scope['operating_or_commercial_clearance']=True;record.write_text(json.dumps(scope))
            with self.assertRaises(ValueError):authorize_inputs(intake,record)
            scope['operating_or_commercial_clearance']=False;record.write_text(json.dumps(scope))
            evidence.write_text('changed evidence')
            with self.assertRaises(ValueError):authorize_inputs(intake,record)
            evidence.write_text('fixture prior research instruction');(models/'info.txt').write_text('changed input')
            with self.assertRaises(ValueError):authorize_inputs(intake,record)


if __name__=='__main__':unittest.main()
