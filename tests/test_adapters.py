import copy
import unittest
from dataclasses import replace

import numpy as np

from validation_v03.adapters import InputSpec,adapt_segment,adapt_session,normalize_frame,compare_contiguous_blocks


def points():
    # Hand-built non-degenerate 2D bones. No participant coordinates.
    p=[[0.,0.] for _ in range(21)]
    for base,x in ((1,-.6),(5,-.4),(9,0.),(13,.4),(17,.7)):
        for offset in range(4):p[base+offset]=[x+.03*offset,.7+.3*offset]
    return p


def frames(times=(0.,100.,200.)):
    rows=[]
    for t in times:
        p=points();p[8][0]+=(t/1000)**2
        rows.append({'t':t,'lm':p})
    return rows


class AdapterTests(unittest.TestCase):
    def spec(self,**changes):return replace(InputSpec(100,100,'pixel_xy','ms',False,.2),**changes)

    def test_aspect_ratio_conversion_recovers_the_same_geometry(self):
        pixel=np.array(points())*100+np.array([300.,100.])
        a=normalize_frame((pixel/np.array([640.,480.])).tolist(),self.spec(width=640,height=480,coordinate_space='normalized_xy'))
        b=normalize_frame((pixel/np.array([1280.,720.])).tolist(),self.spec(width=1280,height=720,coordinate_space='normalized_xy'))
        np.testing.assert_allclose(a[0],b[0]);np.testing.assert_allclose(a[1],b[1],atol=1e-6)

    def test_mirror_is_explicit_and_applied_once_without_mutating_input(self):
        p=points();before=copy.deepcopy(p)
        a=normalize_frame(p,self.spec())[0];b=normalize_frame(p,self.spec(mirror_x=True))[0]
        np.testing.assert_allclose(np.array(a)[:,0],-np.array(b)[:,0]);np.testing.assert_allclose(np.array(a)[:,1],np.array(b)[:,1])
        self.assertEqual(p,before)

    def test_ms_and_seconds_are_equivalent(self):
        a=adapt_segment(frames(),self.spec())
        b=adapt_segment([{'t':r['t']/1000,'lm':r['lm']} for r in frames()],self.spec(time_unit='s'))
        self.assertEqual(a,b);self.assertEqual(a['blocks'][0]['times_seconds'],[0.,.1,.2])

    def test_null_and_gap_split_blocks_and_preserve_all_denominators(self):
        rows=frames();rows+=[{'t':300.,'lm':None}]+frames((400.,500.,600.))+frames((1000.,1100.))
        report=adapt_segment(rows,self.spec())
        self.assertEqual(report['attempted_frames'],9);self.assertEqual(report['missing_frames'],1)
        self.assertEqual(report['analyzed_frames'],6);self.assertEqual(report['excluded_short_block_frames'],2)
        self.assertEqual(report['gap_boundary_count'],1);self.assertEqual(len(report['blocks']),2)

    def test_invalid_geometry_is_not_imputed_and_all_failure_segments_remain(self):
        rows=frames();rows[1]['lm']=[[0.,0.]]*21
        report=adapt_segment(rows,self.spec())
        self.assertEqual(report['invalid_geometry_frames'],1);self.assertEqual(report['analyzed_frames'],0)
        session=adapt_session({'segments':[{'frames':[{'t':0,'lm':None}]}]},self.spec())
        self.assertEqual(session['attempted_frames'],1);self.assertEqual(session['analyzed_frames'],0)

    def test_segment_time_reset_is_preserved_but_within_segment_duplicates_fail(self):
        self.assertEqual(len(adapt_session({'segments':[{'frames':frames()},{'frames':frames()}]},self.spec())['segments']),2)
        for rows in (frames((0,0,1)),frames((10,5,20)),[{'lm':points()}]):
            with self.assertRaises(ValueError):adapt_segment(rows,self.spec())

    def test_unknown_dimensions_units_and_mirror_policy_are_rejected(self):
        for changes in ({'width':0},{'height':float('nan')},{'coordinate_space':'unknown'},
                        {'time_unit':'frames'},{'mirror_x':None},{'max_gap_seconds':0}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.spec(**changes)

    def test_identity_pair_has_zero_candidate_error_without_inventing_a_score(self):
        block=adapt_segment(frames(),self.spec())['blocks'][0]
        result=compare_contiguous_blocks(block,block,dtw_radius=1,max_gap_seconds=.2)
        self.assertEqual(result['dtw_angle_distance'],0.);self.assertEqual(result['angle_phase_grid_mae_degrees'],0.)
        self.assertEqual(result['acceleration_phase_aligned_mae_hand_lengths_per_second_squared'],0.)
        self.assertIsNone(result['score'])

    def test_actual_time_changes_acceleration_without_changing_angular_dtw(self):
        block=adapt_segment(frames(),self.spec())['blocks'][0];slower=copy.deepcopy(block)
        slower['times_seconds']=[t*2 for t in block['times_seconds']]
        result=compare_contiguous_blocks(block,slower,dtw_radius=1,max_gap_seconds=.3)
        self.assertEqual(result['dtw_angle_distance'],0.)
        self.assertGreater(result['acceleration_phase_aligned_mae_hand_lengths_per_second_squared'],0.)

    def test_boolean_strings_and_nonfinite_xy_are_invalid_geometry(self):
        for value in (True,'1.0',float('inf')):
            rows=frames();rows[1]['lm'][8][0]=value
            with self.subTest(value=value):
                self.assertEqual(adapt_segment(rows,self.spec())['invalid_geometry_frames'],1)

    def test_cli_requires_metadata_and_refuses_to_overwrite_private_output(self):
        import json,subprocess,sys,tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'session.json';output=Path(directory)/'private_features.json'
            source.write_text(json.dumps({'experimentInfo':{'participantId':'not-for-export'},
                                         'segments':[{'frames':frames()}]}),encoding='utf8')
            args=[sys.executable,'-m','validation_v03.adapters','--input',str(source),'--output',str(output),
                  '--width','100','--height','100','--coordinate-space','pixel_xy','--time-unit','ms',
                  '--mirror-x','no','--max-gap-seconds','.2']
            result=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            before=output.read_bytes();self.assertNotIn('not-for-export',before.decode('utf8'))
            self.assertEqual(json.loads(before)['attempted_frames'],3)
            self.assertNotEqual(subprocess.run(args,capture_output=True).returncode,0)
            self.assertEqual(output.read_bytes(),before)
            missing=args[:args.index('--width')]
            self.assertNotEqual(subprocess.run(missing,capture_output=True).returncode,0)


if __name__=='__main__':unittest.main()
