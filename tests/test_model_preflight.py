import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from analysis.runtime_benchmark.model_preflight import inspect


class ModelPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.assets=self.root/'assets';self.assets.mkdir()
        self.output=self.root/'private_artifacts'/'preflight'
        self.patch=patch('analysis.runtime_benchmark.model_preflight.REPO',self.root/'repo')
        self.patch.start();self.addCleanup(self.patch.stop)

    def test_missing_inputs_reported_without_model_import_or_install(self):
        result=inspect('hamer_core',self.assets,self.output)
        self.assertEqual(result['state'],'UNAVAILABLE_MISSING_CORE_ASSETS')
        self.assertEqual(len(result['missing']),3);self.assertFalse(result['inference_ready'])
        self.assertFalse(result['weights_deserialized'])

    def test_core_presence_is_never_misreported_as_valid_model_or_inference_ready(self):
        for name in ('_DATA/data/mano/MANO_RIGHT.pkl','_DATA/hamer_ckpts/checkpoints/hamer.ckpt','_DATA/hamer_ckpts/model_config.yaml'):
            path=self.assets/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'synthetic-not-valid-model')
        result=inspect('hamer_core',self.assets,self.output)
        self.assertEqual(result['state'],'CORE_ASSETS_PRESENT_NOT_LOADED')
        self.assertFalse(result['actual_revision_verified']);self.assertFalse(result['inference_ready'])
        self.assertEqual(len(result['files']),3)

    def test_unknown_profile_public_output_and_existing_report_rejected(self):
        with self.assertRaises(ValueError):inspect('unknown',self.assets,self.output)
        with self.assertRaises(ValueError):inspect('hamer_core',self.assets,self.root/'repo'/'report')
        inspect('hamer_core',self.assets,self.output)
        with self.assertRaises(FileExistsError):inspect('hamer_core',self.assets,self.output)
