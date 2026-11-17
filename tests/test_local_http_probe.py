import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import time

from analysis.runtime_benchmark import local_http_probe as probe


def frames():
    return [dict(t_ms=i*100,lm=None if i==1 else [[.1+j*.01+i*.001,.2+j*.01] for j in range(21)]) for i in range(4)]


class LocalHTTPProbeTests(unittest.TestCase):
    def test_candidates_preserve_original_times_missing_mask_and_independent_storage(self):
        original=frames();before=copy.deepcopy(original);cases=probe.make_cases(original)
        self.assertEqual(original,before);reference,static=cases[0][1],cases[1][1]
        self.assertEqual([f['t_ms'] for f in static],[f['t_ms'] for f in reference])
        self.assertEqual([f['lm'] is None for f in static],[f['lm'] is None for f in reference])
        self.assertTrue(all(f['lm']==reference[0]['lm'] for f in static if f['lm'] is not None))
        static[0]['lm'][0][0]=99
        self.assertNotEqual(static[2]['lm'][0][0],99);self.assertEqual(original,before)

    def test_missing_detection_and_invalid_reference_are_not_repaired(self):
        for data in ([dict(t_ms=0,lm=None)],[dict(t_ms=0,lm=[[0,0]]*21)],list(reversed(frames()))):
            with self.assertRaises(ValueError):probe.make_cases(data)

    def test_schema_control_keeps_denial_separate_from_score_and_action(self):
        requests=[]
        class Client:
            def post(self,path,payload):
                requests.append((path,payload));self.last_body_received_ns=time.perf_counter_ns()
                return (200,dict(challenge_id='test')) if path.endswith('challenge') else (400,dict(error='invalid_request'))
        result=probe.schema_control(Client(),frames())
        self.assertEqual(result['submit_http_status'],400);self.assertIsNone(result['score_pass'])
        self.assertIsNone(result['protected_action_allowed']);self.assertTrue(requests[-1][1]['passed'])
        self.assertEqual(len(requests),2)

    def setup_source(self,root):
        source=root/'source';source.mkdir();html=b'owned synthetic unit source, no JS executed'
        (source/'hand_captcha_prod.html').write_bytes(html);(source/'video.mp4').write_bytes(b'synthetic media')
        (source/'coordinates.json').write_text('{}')
        clips=[dict(clip_id='fixture',video_file='video.mp4',landmarks_file='coordinates.json')]
        (source/'pool_manifest.json').write_text(json.dumps(dict(clips=clips)))
        return source,hashlib.sha256(html).hexdigest(),clips

    def test_real_http_runner_with_explicit_stub_evaluator_saves_eight_reconcilable_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source,digest,clips=self.setup_source(root)
            class Evaluator:
                source_root=source;sources={'fixture':{}};closed=False;stderr_tail=[];calls=0
                def frames(self,key):return frames()
                def evaluate(self,*args):
                    self.calls+=1
                    return dict(gate_pass=self.calls==1,score_pass=True,score={'captcha':.8})
                def close(self):self.closed=True
            evaluator=Evaluator();evaluator.clips={'fixture':clips[0]}
            with patch.object(probe,'PROD_SHA256',digest),patch.object(probe,'ActualEvaluator',return_value=evaluator) as factory:
                result=probe.run(source,root/'run')
                factory.assert_called_once_with(source,call_timeout=15)
            self.assertTrue(evaluator.closed);self.assertEqual(evaluator.calls,2)
            self.assertEqual(len(list((root/'run').iterdir())),8)
            self.assertEqual(result['matched_requests_n'],11)
            attempts=json.loads((root/'run/attempts.private.json').read_text())['cases']
            self.assertTrue(attempts[0]['protected_action_allowed']);self.assertFalse(attempts[0]['repeat_action_allowed'])
            self.assertFalse(attempts[1]['server_grant_issued']);self.assertIsNone(attempts[1]['issue_to_action_body_received_ns'])
            self.assertEqual(attempts[2]['submit_http_status'],400)
            joined=json.loads((root/'run/joined.private.json').read_text())
            control=joined['requests'][-1]['server']
            self.assertEqual(control['http_status'],400)
            self.assertNotIn('evaluator',[p['name'] for p in control['phases']])

    def test_prod_hash_and_existing_output_fail_before_evaluator(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source,digest,clips=self.setup_source(root)
            with patch.object(probe,'ActualEvaluator') as factory:
                with self.assertRaises(ValueError):probe.run(source,root/'run')
                self.assertFalse((root/'run').exists())
                (root/'run').mkdir()
                with self.assertRaises(FileExistsError):probe.run(source,root/'run')
                factory.assert_not_called()


if __name__=='__main__':unittest.main()
