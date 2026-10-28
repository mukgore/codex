"""Run the actual-code HTTP and mask regression suites, retaining evidence."""
import argparse
import io
import json
from pathlib import Path
import time
import unittest

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--log',type=Path,required=True);args=parser.parse_args()
    if args.output.exists() or args.log.exists():raise FileExistsError('preserve previous check results')
    suite=unittest.defaultTestLoader.loadTestsFromNames(['g4_lab.test_integration','g4_lab.test_masking'])
    stream=io.StringIO();started=time.perf_counter()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.log.parent.mkdir(parents=True,exist_ok=True)
    args.log.write_text(stream.getvalue(),encoding='utf-8')
    summary={'run_id':'G4-REGRESSION-001','tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'passed':result.wasSuccessful(),'wall_s':time.perf_counter()-started,'suites':['actual_html_loopback_integration','fail_closed_2d_masking'],'scope':'code and fixture verification; no human or source holdout evaluation'}
    args.output.write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary))
    raise SystemExit(0 if result.wasSuccessful() else 1)
if __name__=='__main__':main()
