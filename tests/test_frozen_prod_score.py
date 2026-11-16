import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PROD=ROOT.parent/'handcaptcha-ui-20261113/hand_captcha_prod.html'
NODE=shutil.which('node') or 'C:/Program Files/nodejs/node.exe'
BRIDGE=ROOT/'validation_v03/frozen_prod_score.cjs'


@unittest.skipUnless(PROD.exists(),'Pinned local production source is private workspace input')
class FrozenProdTests(unittest.TestCase):
    def invoke(self,cases,prod=PROD):
        return subprocess.run([NODE,str(BRIDGE),str(prod)],input=json.dumps({'cases':cases}),
                              capture_output=True,text=True,encoding='utf-8',timeout=15)

    def frames(self):
        points=[[.5,.85]]
        for finger in range(5):
            points.extend([[.25+.12*finger+.005*j,.7-.12*j] for j in range(4)])
        return [points for _ in range(25)]

    def test_complete_static_and_missing_detection_factor(self):
        base=self.frames()
        cases=[{'id':str(n),'base':base,'response':[f if i<n else None for i,f in enumerate(base)]}
               for n in (25,13,7,2,0)]
        result=self.invoke(cases);self.assertEqual(result.returncode,0,result.stderr)
        data=json.loads(result.stdout)
        for r,n in zip(data['results'],(25,13,7,2,0)):
            s=r['score'];self.assertFalse(r['hold_validated']);self.assertFalse(r['authentication_validated'])
            self.assertAlmostEqual(s['captcha'],n/25 if n>=3 else 0,places=12)
            self.assertEqual(s['dC'],n if n>=3 else 0)
        self.assertTrue(data['results'][2]['score_threshold_met'])
        self.assertEqual(data['constants']['MATCH_HOLD_MS'],200)
        self.assertEqual(len(data['extraction']['ranges']),4)

    def test_source_drift_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'changed.html';path.write_bytes(PROD.read_bytes()+b'\n')
            r=self.invoke([],path);self.assertNotEqual(r.returncode,0)
            self.assertIn('Pinned production bytes required',r.stderr)

    def test_malformed_and_nonfinite_inputs_rejected(self):
        for response in ([[[0,0]]]*25, self.frames()[:2]):
            r=self.invoke([{'base':self.frames(),'response':response}]);self.assertNotEqual(r.returncode,0)

    def test_moving_self_can_have_nonzero_sliding_window_error(self):
        base=json.loads(json.dumps(self.frames()))
        for i,frame in enumerate(base):
            frame[11][0]+=.1*(i/24)**2;frame[12][0]+=.18*(i/24)**2
        r=self.invoke([{'base':base,'response':base,'mode':'auto_keyframes'}])
        self.assertEqual(r.returncode,0,r.stderr);s=json.loads(r.stdout)['results'][0]['score']
        self.assertEqual(s['rA'],0);self.assertEqual(s['rAc'],0)
        self.assertGreater(s['rDA'],0);self.assertLess(s['captcha'],1)
