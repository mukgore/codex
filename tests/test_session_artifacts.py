import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from validation_v03.session_artifacts import POLICY, decode, inspect, load, save


def bridge():
    return {'schema_version':1,'scope':'local_selection_events_only','policy':copy.deepcopy(POLICY),
            'dropped_events':0,'aborted':False,'events':[
                {'t_ms':100,'event':'selected','reason':'stable_largest_hand','phase':'matching'},
                {'t_ms':200,'event':'completed','reason':'original_score_flow','phase':'done'},
                {'t_ms':200,'event':'phase_changed','reason':'original_flow','phase':'done'}]}


def legacy():
    points=[[i*.01,i*.01,i*.01] for i in range(21)]
    return {'experimentInfo':{'version':'prod_v2_pool','participantId':'PRIVATE_TEST_ONLY'},
            'keyframes':[], 'segments':[{'frames':[{'t':0,'lm':points},{'t':10,'lm':None}],
                                        'totalFrames':2,'detectedFrames':1,'duration':10}],
            'scores':{'totalFrames':2,'detectedFrames':1,'detectionRate':.5},
            'sessionLog':[{'t':0,'phase':'matching','detected':True,'lm':points},
                          {'t':10,'phase':'recording','detected':False,'lm':None}]}


class SessionArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)/'private_artifacts';self.root.mkdir()

    def test_exact_source_and_canonical_round_trip_without_mutating_original(self):
        source=self.root/'original.json';payload=legacy()
        raw=b'\xef\xbb\xbf'+json.dumps(payload,indent=2).encode();source.write_bytes(raw)
        result=save(source,self.root/'artifact');restored,inspection=load(self.root/'artifact')
        self.assertEqual(source.read_bytes(),raw)
        self.assertEqual((self.root/'artifact/source.json').read_bytes(),raw)
        self.assertEqual(restored,payload);self.assertEqual(result,inspection)
        self.assertEqual(result['missing_segment_frames_n'],1)
        self.assertNotIn('PRIVATE_TEST_ONLY',json.dumps(result))
        self.assertIsNone(result['camera_frame_coverage'])
        self.assertFalse(result['input_source_authenticated'])

    def test_changes_to_each_saved_component_are_detected(self):
        for component in ('source.json','canonical.json','receipt.json'):
            source=self.root/'input.json';source.write_text(json.dumps(bridge()))
            folder=self.root/component.replace('.','_');save(source,folder)
            path=folder/component;path.write_bytes(path.read_bytes()+b' ')
            if component=='receipt.json':
                receipt=json.loads(path.read_text());receipt['inspection']['saved_events_n']=999
                path.write_text(json.dumps(receipt))
            with self.subTest(component=component),self.assertRaises(ValueError):load(folder)

    def test_partial_artifact_and_overwrite_are_rejected(self):
        source=self.root/'input.json';source.write_text(json.dumps(bridge()))
        folder=self.root/'artifact';save(source,folder)
        before=(folder/'source.json').read_bytes()
        with self.assertRaises(FileExistsError):save(source,folder)
        self.assertEqual(before,(folder/'source.json').read_bytes())
        (folder/'receipt.json').unlink()
        with self.assertRaises(OSError):load(folder)

    def test_receipt_whitespace_or_python_equal_but_different_json_type_is_rejected(self):
        source=self.root/'input.json';source.write_text(json.dumps(bridge()))
        for index,change in enumerate([lambda raw:raw+b' ',
                                      lambda raw:raw.replace(b'"artifact_version":1',b'"artifact_version":true'),
                                      lambda raw:raw.replace(b'"saved_events_n":3',b'"saved_events_n":3.0')]):
            folder=self.root/f'typed_{index}';save(source,folder)
            receipt=folder/'receipt.json';before=receipt.read_bytes();after=change(before)
            self.assertNotEqual(before,after);receipt.write_bytes(after)
            with self.subTest(index=index),self.assertRaises(ValueError):load(folder)

    def test_coordinate_payload_unknown_policy_and_nonboolean_flags_are_rejected(self):
        for mutate in [lambda p:p['events'][0].update(lm=[[0,0]]*21),
                       lambda p:p['policy'].update(maxGateGapMs=201),
                       lambda p:p['policy'].update(maxGateGapMs=200.),
                       lambda p:p.update(aborted='False'),
                       lambda p:p['events'][0].update(reason='private-filename')]:
            payload=bridge();mutate(payload)
            with self.assertRaises(ValueError):inspect(payload)

    def test_truncation_never_becomes_full_log_evidence(self):
        payload=bridge();payload['dropped_events']=100
        result=inspect(payload)
        self.assertEqual(result['reconstruction_status'],'TRUNCATED_PARTIAL_LOG')
        self.assertFalse(result['score_observed'])

    def test_terminal_postprocessing_is_allowed_but_conflicting_terminals_are_not(self):
        self.assertEqual(inspect(bridge())['observed_terminal_events'],{'completed':1})
        payload=bridge();payload['events'].append({'t_ms':201,'event':'aborted','reason':'timeout','phase':'done'})
        payload['aborted']=True
        with self.assertRaises(ValueError):inspect(payload)

    def test_duplicate_keys_nan_overflow_reversed_clock_and_string_boolean_rejected(self):
        for raw in [b'{"x":1,"x":2}',b'{"x":NaN}',b'{"x":1e9999}']:
            with self.assertRaises(ValueError):decode(raw)
        payload=bridge();payload['events'][1]['t_ms']=99
        with self.assertRaises(ValueError):inspect(payload)
        payload=legacy();payload['sessionLog'][1]['detected']='False'
        with self.assertRaises(ValueError):inspect(payload)

    def test_legacy_counts_and_geometry_shapes_are_checked(self):
        for mutate in [lambda p:p['scores'].update(detectedFrames=2),
                       lambda p:p['scores'].update(detectionRate=.9),
                       lambda p:p['segments'][0]['frames'][0].update(lm=[[0,0]]*21),
                       lambda p:p['segments'][0]['frames'][1].update(t=0)]:
            payload=legacy();mutate(payload)
            with self.assertRaises(ValueError):inspect(payload)

    def test_actual_javascript_snapshot_round_trips(self):
        source=Path(os.environ.get('HANDCAPTCHA_SOURCE_ROOT',Path(__file__).resolve().parents[2]/'handcaptcha'))
        module=(source/'experiments/hand_selection/session_log.js').resolve()
        if not module.is_file():self.skipTest('Owned handcaptcha checkout required for actual-JS integration')
        code="const {SessionLog}=require(process.argv[1]);let t=0;let s=new SessionLog({clock:()=>t,limit:2});s.record('selected');t=10;s.record('lost');t=20;s.record('reselect');process.stdout.write(JSON.stringify(s.snapshot()));"
        result=subprocess.run(['node','-e',code,str(module)],capture_output=True,check=True)
        source=self.root/'js.json';source.write_bytes(result.stdout)
        inspection=save(source,self.root/'actual_js')
        self.assertEqual(inspection['format'],'palm_guidance_v1')
        self.assertTrue(inspection['truncated'])
        self.assertEqual(inspection['saved_events_n'],2)

    def test_cli_verify_rejects_corruption_without_echoing_payload(self):
        source=self.root/'input.json';source.write_text(json.dumps(legacy()))
        folder=self.root/'artifact';save(source,folder)
        args=[sys.executable,'-m','validation_v03.session_artifacts','--verify',str(folder)]
        result=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        (folder/'source.json').write_text('PRIVATE_TEST_ONLY')
        result=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertNotIn('PRIVATE_TEST_ONLY',result.stderr)


if __name__=='__main__':unittest.main()
