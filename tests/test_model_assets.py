import os
from pathlib import Path
import pickle
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from analysis.runtime_benchmark.model_assets import stage_mano


class ModelAssetTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.repo_patch=patch('analysis.runtime_benchmark.model_assets.REPO',self.root/'repo')
        self.repo_patch.start();self.addCleanup(self.repo_patch.stop)
        self.output=self.root/'private_artifacts'/'run'

    def archive(self, extras=None):
        path=self.root/'mano.zip'
        rows={'mano/models/MANO_RIGHT.pkl':b'synthetic-not-a-real-model',
              'mano/models/MANO_LEFT.pkl':b'synthetic-not-a-real-model',
              'mano/models/LICENSE.txt':b'synthetic-license-fixture-not-permission'}
        rows.update(extras or {})
        with zipfile.ZipFile(path,'w') as archive:
            for name,data in rows.items():archive.writestr(name,data)
        return path

    def test_stages_both_models_and_license_without_false_validation(self):
        report=stage_mano(self.archive(),self.output)
        self.assertEqual(report['state'],'FILES_STAGED_NOT_LOADED');self.assertFalse(report['release_allowed'])
        self.assertEqual(report['rights_status'],'UNREVIEWED');self.assertEqual(len(report['files']),3)
        with self.assertRaises(FileExistsError):stage_mano(self.root/'mano.zip',self.output)

    def test_pickle_is_copied_as_bytes_never_executed(self):
        sentinel=self.root/'must_not_exist'
        class Payload:
            def __reduce__(self):return (os.mkdir,(str(sentinel),))
        data=pickle.dumps(Payload())
        stage_mano(self.archive({'mano/models/MANO_RIGHT.pkl':data}),self.output)
        self.assertFalse(sentinel.exists())
        self.assertEqual((self.output/'models'/'MANO_RIGHT.pkl').read_bytes(),data)

    def test_traversal_duplicate_roles_and_wrong_destination_rejected(self):
        for extra in ({'../escape':b'bad'},{'other/MANO_RIGHT.pkl':b'duplicate'},{'C:/device':b'bad'}):
            with self.assertRaises(ValueError):stage_mano(self.archive(extra),self.output)
            self.assertFalse(self.output.exists())
        with self.assertRaises(ValueError):stage_mano(self.archive(),self.root/'repo'/'public_models')

    def test_missing_license_and_split_versions_rejected(self):
        path=self.root/'missing.zip'
        with zipfile.ZipFile(path,'w') as archive:
            archive.writestr('models/MANO_LEFT.pkl',b'left');archive.writestr('models/MANO_RIGHT.pkl',b'right')
        with self.assertRaises(ValueError):stage_mano(path,self.output)
