from pathlib import Path
from types import SimpleNamespace
import unittest
from analysis.mediapipe_matched_metrics import evaluate
from analysis.runtime_benchmark.mediapipe_video_worker import relative_resources


class MediaPipeMatchedTests(unittest.TestCase):
    def series(self,missing=0):
        names=[f'P{i}' for i in range(21)]
        truth=[];predicted=[]
        points={n:{'x':100.+i,'y':250.} for i,n in enumerate(names)}
        points[names[0]]={'x':200.,'y':300.};points[names[9]]={'x':200.,'y':200.}
        for i in range(25):
            truth.append({'frame_idx':i,'source_pts_ms':i*125.,'landmarks_px':points})
            predicted.append({'frame_idx':i,'source_pts_ms':i*125.,'detected':i>=missing,
              'landmarks_px':{n:{'x':p['x']+3,'y':p['y']+4} for n,p in points.items()}})
        return truth,predicted,names

    def test_missing_frames_stay_in_denominator_without_fabricated_zero_errors(self):
        t,p,n=self.series(12);r=evaluate(t,p,n)
        self.assertEqual(r['detected_frames_n'],13);self.assertEqual(r['missing_frames_n'],12)
        self.assertEqual(r['detected_point_comparisons_n'],13*21)
        self.assertAlmostEqual(r['conditional_mean_point_error_pixels'],5.)
        self.assertAlmostEqual(r['conditional_mean_error_reference_hand_lengths'],.05)
        self.assertIsNone(r['per_frame'][0]['error_mean_pixels'])
        t,p,n=self.series(25);r=evaluate(t,p,n)
        self.assertIsNone(r['conditional_mean_point_error_pixels']);self.assertEqual(r['detected_fraction'],0.)

    def test_actual_reference_grid_and_finite_predictions_are_required(self):
        t,p,n=self.series();p[5]['source_pts_ms']+=1
        with self.assertRaises(ValueError):evaluate(t,p,n)
        t,p,n=self.series();p[0]['landmarks_px'][n[0]]['x']=float('nan')
        with self.assertRaises(ValueError):evaluate(t,p,n)
        with self.assertRaises(ValueError):evaluate(t[:-1],p,n)

    def test_degenerate_reference_scale_is_missing_normalized_error_not_zero(self):
        t,p,n=self.series()
        for f in t:f['landmarks_px'][n[9]]=dict(f['landmarks_px'][n[0]])
        r=evaluate(t,p,n);self.assertEqual(r['reference_scale_invalid_detected_frames_n'],25)
        self.assertIsNone(r['conditional_mean_error_reference_hand_lengths'])

    def test_ascii_resource_patch_is_process_local_and_restored_on_errors(self):
        previous=object();module=SimpleNamespace(os=previous,__file__='original_solution_base.py')
        root=Path.cwd().parent/'private_artifacts'/'fake_ascii_resources'
        with relative_resources(module,root):
            self.assertIsNot(module.os,previous)
            self.assertTrue(module.os.path.abspath(module.__file__).isascii())
        self.assertIs(module.os,previous)
        with self.assertRaises(RuntimeError):
            with relative_resources(module,root):raise RuntimeError('synthetic constructor failure')
        self.assertIs(module.os,previous)
