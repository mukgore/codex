import copy
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from analysis.runtime_benchmark.matched_display_bundle import repeat_static
from analysis.runtime_benchmark.mano_common_camera_rerender import read_frozen_camera,validate_frozen_bundle


class MatchedDisplayTests(unittest.TestCase):
    def test_static_reuse_keeps_every_point_and_exact_25_frame_denominator(self):
        original=np.arange(63,dtype=np.float32).reshape(1,21,3)
        repeated=repeat_static(original);self.assertEqual(repeated.shape,(25,21,3))
        for frame in repeated:np.testing.assert_array_equal(frame,original[0])
        with self.assertRaises(ValueError):repeat_static(np.zeros((2,21,3)))
        with self.assertRaises(ValueError):repeat_static(np.full((1,21,3),np.nan))

    def test_frozen_camera_keeps_exact_existing_parameters_and_rejects_reflection(self):
        camera={'width':512,'height':420,'pixels_per_native_unit':100.,'center_base':[0.,1.],
          'basis_columns':np.eye(3).tolist(),'pixel_origin':[256,210],'fit_scope':'test-existing-camera'}
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'private_artifacts';root.mkdir()
            p=root/'frozen_camera.private.json';p.write_text(json.dumps(camera))
            self.assertEqual(read_frozen_camera(p),camera)
            changed=copy.deepcopy(camera);changed['basis_columns'][0][0]=-1;p.write_text(json.dumps(changed))
            with self.assertRaises(ValueError):read_frozen_camera(p)
            changed=copy.deepcopy(camera);changed['pixels_per_native_unit']=0;p.write_text(json.dumps(changed))
            with self.assertRaises(ValueError):read_frozen_camera(p)

    def test_four_arm_source_cannot_change_protection_mode_or_silently_omit_model_status(self):
        summary={'version':'tf04_matched_ABC_U_native_bundle_v1',
          'cases':[{'arm':arm,'model_surface_eligible_for_display_comparison':arm!='U'} for arm in ('A','B','C','U') for _ in range(4)]}
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder).resolve()/'private_artifacts';source.mkdir();camera=source/'frozen_camera.private.json'
            validate_frozen_bundle(summary,source,camera,'hand_neutral_registered','author_region_union')
            with self.assertRaises(ValueError):validate_frozen_bundle(summary,source,None,'hand_neutral_registered','author_region_union')
            with self.assertRaises(ValueError):validate_frozen_bundle(summary,source,camera,'hand_neutral_registered','legacy_rest_proxy')
            broken=copy.deepcopy(summary);del broken['cases'][0]['model_surface_eligible_for_display_comparison']
            with self.assertRaises(ValueError):validate_frozen_bundle(broken,source,camera,'hand_neutral_registered','author_region_union')
            with self.assertRaises(ValueError):validate_frozen_bundle(summary,source,source/'other.json','hand_neutral_registered','author_region_union')
