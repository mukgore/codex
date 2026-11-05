from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import unittest

import numpy as np
from validation_v03.adapters import InputSpec, adapt_segment, compare_contiguous_blocks
from validation_v03.standard_metrics import constrained_dtw
from test_adapters import frames


class RawJSParityTests(unittest.TestCase):
    def js(self, request, *, valid=True):
        script=Path(__file__).resolve().parents[1]/'validation_v03'/'raw_features.cjs'
        result=subprocess.run(['node',str(script)],input=json.dumps(request),capture_output=True,text=True,timeout=10)
        if not valid:
            self.assertNotEqual(result.returncode,0);return
        self.assertEqual(result.returncode,0,result.stderr);return json.loads(result.stdout)

    def test_units_mirror_gap_missing_and_invalid_geometry_match(self):
        for mirror in (True,False):
            for unit in ('ms','s'):
                spec=InputSpec(640,480,'pixel_xy',unit,mirror,.2)
                rows=frames((0,90,200,300,400,500,900,1000))
                rows[3]['lm']=None;rows[6]['lm']=[[0,0]]*21
                if unit=='s': rows=[{**row,'t':row['t']/1000} for row in rows]
                expected=adapt_segment(rows,spec)
                actual=self.js(dict(method='adapt',frames=rows,spec=asdict(spec)))
                for key in expected:
                    if key!='blocks': self.assertEqual(actual[key],expected[key])
                for a,b in zip(actual['blocks'],expected['blocks']):
                    np.testing.assert_allclose(a['normalized_xy'],b['normalized_xy'],atol=1e-12)
                    np.testing.assert_allclose(a['angles_degrees'],b['angles_degrees'],atol=2e-6)

    def test_irregular_time_feature_comparison_matches(self):
        spec=InputSpec(640,480,'pixel_xy','ms',False,.25)
        a=adapt_segment(frames((0,80,190,300,450)),spec)['blocks'][0]
        b=adapt_segment(frames((0,110,240,400,600)),spec)['blocks'][0]
        expected=compare_contiguous_blocks(a,b,dtw_radius=2,max_gap_seconds=.25)
        actual=self.js(dict(method='compare',reference=a,response=b,options=dict(dtw_radius=2,max_gap_seconds=.25)))
        for key in ('angle_phase_grid_mae_degrees','dtw_angle_distance','dtw_angle_path_rmse',
                    'acceleration_phase_aligned_mae_hand_lengths_per_second_squared'):
            self.assertAlmostEqual(actual[key],expected[key],delta=2e-9)
        self.assertIsNone(actual['score'])

    def test_dtw_random_series_and_tie_paths_match(self):
        rng=np.random.default_rng(7)
        for x,y in [([[0],[0],[0]],[[0],[0]])]+[(rng.normal(size=(6,3)).tolist(),rng.normal(size=(5,3)).tolist()) for _ in range(8)]:
            expected=constrained_dtw(x,y,radius=2)
            actual=self.js(dict(method='dtw',x=x,y=y,radius=2))
            self.assertEqual(actual['path'],[list(pair) for pair in expected.path])
            self.assertAlmostEqual(actual['distance'],expected.distance,places=12)

    def test_invalid_times_and_specs_fail_in_both_languages(self):
        spec=InputSpec(640,480,'pixel_xy','ms',False,.2)
        with self.assertRaises(ValueError): adapt_segment(frames((0,0,200)),spec)
        self.js(dict(method='adapt',frames=frames((0,0,200)),spec=asdict(spec)),valid=False)
        self.js(dict(method='adapt',frames=frames(),spec={**asdict(spec),'mirror_x':'yes'}),valid=False)
