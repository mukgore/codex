import copy
import importlib.metadata
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from validation_v03.run_manifest import TEXT_FIELDS, prepare, read, validate_config, verify_current


class RunManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.repo=self.root/'repo';self.repo.mkdir()
        self.private=self.root/'private_artifacts';self.private.mkdir()
        def git(*args):return subprocess.run(['git','-c','safe.directory='+self.repo.as_posix(),'-C',str(self.repo),*args],
                                              check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.git=git;git('init');git('config','user.email','fixture@example.invalid')
        git('config','user.name','Synthetic Fixture');git('config','commit.gpgsign','false')
        (self.repo/'worker.py').write_text('value = 1\n');git('add','worker.py');git('commit','-m','fixture')
        (self.private/'input.json').write_text('{"synthetic": true}')
        self.lock=self.private/'requirements.lock'
        self.lock.write_text('numpy=='+importlib.metadata.version('numpy')+'\n')
        self.config={**{key:'fixture-'+key for key in TEXT_FIELDS},'schema_version':1,
            'execution_scope':'owned_js_fixture','split':'diagnostic','seed':7,'timeout_seconds':30,
            'parameters':{'fixture_only':True},'code_files':['worker.py'],
            'input_files':[{'id':'fixture','role':'synthetic_input','path':'input.json'}],
            'dependency_lock':'requirements.lock','browser':'not_applicable_offline'}
        self.path=self.private/'config.json';self.path.write_text(json.dumps(self.config))

    def freeze(self):return prepare(self.path,self.repo,self.private/'snapshot')

    def test_snapshot_records_actual_code_environment_and_does_not_claim_task_execution(self):
        manifest,fingerprint=self.freeze();restored,other=read(self.private/'snapshot')
        self.assertEqual(manifest,restored);self.assertEqual(fingerprint,other)
        self.assertEqual(manifest['pinned_versions']['numpy'],importlib.metadata.version('numpy'))
        self.assertEqual(len(manifest['code_commit']),40)
        self.assertEqual(len(manifest['dirty_diff_hash']),64)
        result=verify_current(self.private/'snapshot')
        self.assertEqual(result['status'],'CURRENT_SNAPSHOT_MATCHES')
        self.assertFalse(result['task_completion_proven'])

    def test_missing_metadata_placeholders_invalid_seed_and_live_browser_fail(self):
        for key in TEXT_FIELDS:
            config=copy.deepcopy(self.config);config.pop(key)
            with self.subTest(key=key),self.assertRaises(ValueError):validate_config(config)
        for change in [{'seed':None},{'seed':True},{'timeout_seconds':float('inf')},
                       {'execution_scope':'live_camera'},{'hardware':'unknown'},
                       {'input_files':[{'id':'run_config','role':'x','path':'input.json'}]}]:
            config={**self.config,**change}
            with self.subTest(change=change),self.assertRaises(ValueError):validate_config(config)

    def test_wrong_installed_version_and_mutable_dependency_formats_fail(self):
        for text in ['numpy==0.0.0\n','numpy>=1\n','-e ../somewhere\n']:
            self.lock.write_text(text)
            with self.subTest(text=text),self.assertRaises(ValueError):self.freeze()
            self.assertFalse((self.private/'snapshot').exists())

    def test_each_declared_input_or_code_change_is_detected(self):
        for relative in ['input.json','config.json','requirements.lock']:
            with self.subTest(relative=relative):
                folder=self.private/('run-'+relative)
                prepare(self.path,self.repo,folder)
                path=self.private/relative;before=path.read_bytes();path.write_bytes(before+b'\n')
                with self.assertRaises(ValueError):verify_current(folder)
                path.write_bytes(before)
        self.freeze();(self.repo/'worker.py').write_text('value = 2\n')
        with self.assertRaises(ValueError):verify_current(self.private/'snapshot')

    def test_untracked_file_changes_are_part_of_dirty_fingerprint(self):
        path=self.repo/'untracked.py';path.write_text('private fixture\n')
        manifest,_=self.freeze()
        self.assertEqual(manifest['untracked_files'][0]['path'],'untracked.py')
        path.write_text('changed\n')
        with self.assertRaises(ValueError):verify_current(self.private/'snapshot')

    def test_modified_manifest_and_existing_output_are_rejected(self):
        self.freeze()
        with self.assertRaises(FileExistsError):self.freeze()
        path=self.private/'snapshot/manifest.json';path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaises(ValueError):read(self.private/'snapshot')

    def test_declared_code_escape_and_repository_output_are_rejected(self):
        self.config['code_files']=['../private_artifacts/input.json'];self.path.write_text(json.dumps(self.config))
        with self.assertRaises(ValueError):self.freeze()
        with self.assertRaises(ValueError):prepare(self.path,self.repo,self.repo/'private_artifacts/run')


if __name__=='__main__':unittest.main()
