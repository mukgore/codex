import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from analysis.runtime_benchmark.extraction_worker import execute
from analysis.runtime_benchmark.journal import recover_bytes


class ExtractionWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);adapter=self.root/'adapter'/'dataset_pipeline';adapter.mkdir(parents=True)
        for name in ('stage1_extract.py','resource_worker.py','common.py'): (adapter/name).write_bytes(b'# synthetic adapter fixture')
        video=self.root/'input.mp4';video.write_bytes(b'synthetic-integrity-fixture-not-video')
        self.request=dict(condition_id='fixture',planned_frames=3,timeout_seconds=30,cache_state='none',
                          video=str(video),handcaptcha_root=str(adapter.parent),expected_input_sha256=hashlib.sha256(video.read_bytes()).hexdigest())
        self.environment=patch.dict(os.environ,RUNTIME_JOURNAL_DIRECTORY=str(self.root/'journal'))
        self.environment.start();self.addCleanup(self.environment.stop)

    def test_missing_runtime_is_unavailable_without_installing_or_false_error(self):
        original=__import__
        def imports(name,*args,**kwargs):
            if name=='dataset_pipeline.stage1_extract': raise ModuleNotFoundError('synthetic missing runtime')
            return original(name,*args,**kwargs)
        with patch('builtins.__import__',side_effect=imports):
            self.assertEqual(execute(self.request),{'status':'UNAVAILABLE'})
        recovered=recover_bytes((self.root/'journal'/'events.jsonl').read_bytes())
        self.assertEqual(recovered['status'],'UNAVAILABLE')

    def test_changed_input_is_error_before_model_import(self):
        self.request['expected_input_sha256']='0'*64
        with self.assertRaises(ValueError):execute(self.request)
        recovered=recover_bytes((self.root/'journal'/'events.jsonl').read_bytes())
        self.assertEqual(recovered['status'],'ERROR');self.assertEqual(recovered['completed_frames'],0)
