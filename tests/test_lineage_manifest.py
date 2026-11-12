import copy
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from validation_v03.lineage_manifest import audit,validate_score_rows
from validation_v03.run_manifest import snapshot_file


def fixture(directory):
    packet=dict(schema_version=1,data_scope='synthetic_metadata',require_unexposed_test=True,
                sources=[],allocations=[])
    for split in ('development','validation','test'):
        path=Path(directory)/(split+'.bin');path.write_bytes(split.encode())
        packet['sources'].append(dict(source_id=split,path=path.name,parent_ids=[],
            family_ids=[split+'-family'],capture_ids=[split+'-capture'],
            lineage_status='root_of_supplied_material',exposure='declared_unused'))
        packet['allocations'].append(dict(allocation_id=split,split=split,source_ids=[split],
            participant_ids=[split+'-person'],capture_ids=[split+'-response']))
    return packet


class LineageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.packet=fixture(self.base)

    def check(self):return audit(self.packet,base=self.base)

    def codes(self):return self.check()['summary']['declared_constraint_findings']

    def test_disjoint_declarations_pass_without_claiming_independence_or_mutation(self):
        before=copy.deepcopy(self.packet);result=self.check()
        self.assertTrue(result['summary']['declared_constraints_satisfied'])
        self.assertFalse(result['summary']['independence_proven'])
        self.assertFalse(result['summary']['source_authentication_proven'])
        self.assertEqual(before,self.packet)
        summary=json.dumps(result['summary'])
        self.assertNotIn(str(self.base),summary)
        for source in result['private_sources']:
            self.assertNotIn(source['sha256'],summary)
            self.assertNotIn(source['effective_family_ids'][0],summary)

    def test_derived_lineage_catches_renamed_split_leakage(self):
        child=self.packet['sources'][1]
        child.update(parent_ids=['development'],lineage_status='derived',family_ids=['development-family'])
        codes=self.codes()
        for code in ('CROSS_SPLIT_SOURCE_IDENTITY','CROSS_SPLIT_FAMILY','CROSS_SPLIT_CAPTURE','CROSS_SPLIT_BYTE_IDENTITY'):
            self.assertIn(code,codes)

    def test_composite_parents_require_all_families(self):
        self.packet['sources'][2].update(parent_ids=['development','validation'],lineage_status='derived')
        self.assertIn('MISSING_DECLARED_PARENT_FAMILY',self.codes())

    def test_byte_alias_joins_separately_named_roots_and_exposure(self):
        (self.base/'test.bin').write_bytes((self.base/'development.bin').read_bytes())
        self.packet['sources'][0]['exposure']='used_in_development'
        codes=self.codes()
        for code in ('BYTE_ALIAS_FAMILY_CONFLICT','CROSS_SPLIT_BYTE_IDENTITY','EXPOSED_TEST_SOURCE'):
            self.assertIn(code,codes)

    def test_unallocated_public_alias_blocks_test(self):
        alias=copy.deepcopy(self.packet['sources'][2]);alias.update(source_id='unallocated',exposure='known_public')
        self.packet['sources'].append(alias)
        self.assertIn('EXPOSED_TEST_SOURCE',self.codes())

    def test_unknown_exposure_and_unresolved_metadata_are_not_silently_accepted(self):
        self.packet['sources'][2].update(exposure='unknown',lineage_status='unresolved',family_ids=[],capture_ids=[])
        codes=self.codes()
        for code in ('UNVERIFIED_TEST_EXPOSURE','UNRESOLVED_PARENT_LINEAGE','UNRESOLVED_SOURCE_FAMILY','UNRESOLVED_CAPTURE_LINEAGE'):
            self.assertIn(code,codes)

    def test_declared_unused_child_inherits_development_exposure(self):
        self.packet['sources'][0]['exposure']='used_in_development'
        self.packet['sources'][2].update(parent_ids=['development'],lineage_status='derived',family_ids=['development-family'])
        self.assertIn('EXPOSED_TEST_SOURCE',self.codes())

    def test_participant_capture_overlap_and_namespace_separation(self):
        self.packet['allocations'][2]['participant_ids']=['development-family']
        self.assertTrue(self.check()['summary']['declared_constraints_satisfied'])
        self.packet['allocations'][2]['participant_ids']=['development-person']
        self.packet['allocations'][2]['capture_ids']=['development-response']
        self.assertIn('CROSS_SPLIT_PARTICIPANT',self.codes())
        self.assertIn('CROSS_SPLIT_CAPTURE',self.codes())

    def test_invalid_parent_graphs_and_hash_claims_rejected(self):
        original=copy.deepcopy(self.packet)
        for update in (dict(parent_ids=['missing'],lineage_status='derived'),
                       dict(parent_ids=[],lineage_status='derived'),dict(sha256='incorrect')):
            self.packet=copy.deepcopy(original);self.packet['sources'][0].update(update)
            with self.subTest(update=update),self.assertRaises(ValueError):self.check()
        self.packet=copy.deepcopy(original)
        self.packet['sources'][0].update(parent_ids=['test'],lineage_status='derived')
        self.packet['sources'][2].update(parent_ids=['development'],lineage_status='derived')
        with self.assertRaisesRegex(ValueError,'Cyclic'):self.check()

    def test_byte_identical_parent_child_is_not_a_chronological_cycle(self):
        child=copy.deepcopy(self.packet['sources'][0])
        child.update(source_id='copy',parent_ids=['development'],lineage_status='derived')
        self.packet['sources'].append(child)
        self.assertTrue(self.check()['summary']['declared_constraints_satisfied'])

    def test_file_drift_during_audit_rejected(self):
        calls=0
        def drift(path):
            nonlocal calls
            calls+=1
            if calls==4:(self.base/'development.bin').write_bytes(b'changed')
            return snapshot_file(path)
        with patch('validation_v03.lineage_manifest.snapshot_file',side_effect=drift):
            with self.assertRaisesRegex(ValueError,'changed during'):self.check()

    def test_missing_partitions_and_oversized_id_collections(self):
        self.packet['allocations'].pop()
        self.assertIn('MISSING_INDEPENDENT_PARTITIONS',self.codes())
        self.packet['sources'][0]['family_ids']=[str(n) for n in range(1001)]
        with self.assertRaises(ValueError):self.check()

    def score_rows(self):
        rows=[]
        for allocation in self.packet['allocations']:
            split=allocation['split']
            rows.append(dict(trial_id=split,split=split,source_family_ids=split+'-family',
                participant_id=split+'-person',capture_id=split+'-response',label='human',outcome='scored',
                legacy_score='.9',candidate_score='.9'))
        return rows

    def test_csv_binding_rejects_each_changed_lineage_field(self):
        result=self.check();rows=self.score_rows();validate_score_rows(rows,result)
        for key in ('trial_id','split','source_family_ids','participant_id','capture_id'):
            altered=copy.deepcopy(rows);altered[0][key]='altered'
            with self.subTest(key=key),self.assertRaises(ValueError):validate_score_rows(altered,result)

    def test_comparison_cli_checks_manifest_before_threshold_selection(self):
        rows=self.score_rows()
        # Add an attack trial per split sharing its source, with an independent response capture.
        for row in list(rows):
            attack=dict(row,trial_id=row['trial_id']+'attack',label='attack',participant_id='',
                        capture_id=row['capture_id']+'attack',legacy_score='.1',candidate_score='.1')
            rows.append(attack)
            self.packet['allocations'].append(dict(allocation_id=attack['trial_id'],split=attack['split'],
                source_ids=[attack['split']],participant_ids=[],capture_ids=[attack['capture_id']]))
        source=self.base/'scores.csv';manifest=self.base/'lineage.json';output=self.base/'report.json'
        with source.open('w',encoding='utf8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
        manifest.write_text(json.dumps(self.packet),encoding='utf8')
        args=[sys.executable,'-m','validation_v03.compare_scores','--input',str(source),'--output',str(output),
              '--lineage-manifest',str(manifest),'--min-human-accept','1','--max-attack-accept','0']
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertTrue(json.loads(output.read_text())['lineage_preflight']['declared_constraints_satisfied'])
        output.unlink();self.packet['sources'][2]['exposure']='known_public'
        manifest.write_text(json.dumps(self.packet),encoding='utf8')
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        self.assertIn('no thresholds selected',run.stderr)
        self.assertFalse(output.exists())

    def test_audit_cli_preserves_existing_artifacts_and_sanitizes_failure(self):
        manifest=self.base/'manifest.json';manifest.write_text(json.dumps(self.packet),encoding='utf8')
        output=self.base/'private_artifacts'/'audit'
        args=[sys.executable,'-m','validation_v03.lineage_manifest','--input',str(manifest),'--output',str(output)]
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        before={path.name:path.read_bytes() for path in output.iterdir()}
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,2)
        self.assertNotIn(str(self.base),run.stderr)
        self.assertEqual(before,{path.name:path.read_bytes() for path in output.iterdir()})
        manifest.write_bytes(b'{invalid')
        run=subprocess.run(args,capture_output=True,text=True)
        self.assertEqual(run.returncode,2)
        self.assertEqual(json.loads(run.stderr)['status'],'REJECTED')


if __name__=='__main__':unittest.main()
