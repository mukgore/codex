import copy
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from validation_v03.generated_scene_manifest import AXES, audit
from validation_v03.lineage_manifest import validate_score_rows, audit as lineage_audit
from validation_v03.run_manifest import snapshot_file


def fixture(base):
    (base/'assets.json').write_text('{"scope":"self authored synthetic test, not rights certification"}')
    packet={'schema_version':1,'data_scope':'synthetic_metadata','require_unexposed_test':True,
            'separate_axes':list(AXES),'scenes':[],'sources':[],'allocations':[]}
    for i,split in enumerate(('development','validation','test')):
        (base/(split+'.bin')).write_bytes(split.encode())
        packet['scenes'].append({'scene_id':split,'origin_type':'generated_3d','generator_version':'fixture_v1',
            'generation_run_id':'same-computational-job','seed':i,'parameters':{'fixture':'same-param'},
            'family_axes':{axis:split+'-'+axis for axis in AXES},
            'asset_record':{'path':'assets.json','status':'self_authored_fixture'}})
        packet['sources'].append({'source_id':split,'path':split+'.bin','scene_id':split,'parent_ids':[],
                                 'lineage_status':'root_of_supplied_material','exposure':'declared_unused',
                                 'variant_parameters':{'mode':'synthetic_fixture'}})
        packet['allocations'].append({'allocation_id':split,'split':split,'source_ids':[split],
                                     'participant_ids':[split+'-person'],'capture_ids':[split+'-response']})
    return packet


class GeneratedSceneTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.packet=fixture(self.base)

    def check(self):return audit(self.packet,base=self.base)

    def test_disjoint_declarations_pass_without_inventing_camera_or_semantic_proof(self):
        before=copy.deepcopy(self.packet);result=self.check();s=result['summary']
        self.assertTrue(s['declared_constraints_satisfied']);self.assertEqual(s['source_origin'],'generated_3d')
        self.assertFalse(s['independence_proven']);self.assertFalse(s['rights_or_semantic_independence_proven'])
        self.assertEqual(s['generation_runs_n'],1);self.assertEqual(before,self.packet)
        self.assertNotIn(str(self.base),json.dumps(s))

    def test_distinct_seeds_do_not_hide_each_shared_axis(self):
        before=copy.deepcopy(self.packet)
        for axis in AXES:
            self.packet=copy.deepcopy(before)
            self.packet['scenes'][2]['family_axes'][axis]=self.packet['scenes'][0]['family_axes'][axis]
            result=self.check()
            with self.subTest(axis=axis):
                self.assertFalse(result['summary']['declared_constraints_satisfied'])
                self.assertIn(axis,result['summary']['cross_split_overlap_counts_by_axis'])
                self.assertIn('CROSS_SPLIT_SCENE_AXIS',result['summary']['declared_constraint_findings'])

    def test_partial_holdout_reports_overlap_in_other_axes_without_claiming_full_holdout(self):
        self.packet['separate_axes']=['object_geometry']
        self.packet['scenes'][2]['family_axes']['camera']=self.packet['scenes'][0]['family_axes']['camera']
        s=self.check()['summary'];self.assertTrue(s['declared_constraints_satisfied'])
        self.assertFalse(s['all_six_axes_requested']);self.assertIn('camera',s['cross_split_overlap_counts_by_axis'])

    def test_relabelled_identical_recipe_is_not_a_new_independent_scene(self):
        self.packet['scenes'][2]['seed']=self.packet['scenes'][0]['seed']
        s=self.check()['summary'];self.assertEqual(s['scene_recipe_alias_groups_n'],1)
        self.assertFalse(s['declared_constraints_satisfied']);self.assertIn('CROSS_SPLIT_FAMILY',s['declared_constraint_findings'])

    def test_child_inherits_all_parent_families_and_exposure(self):
        self.packet['sources'][2].update(parent_ids=['development'],lineage_status='derived')
        self.packet['sources'][0]['exposure']='used_in_development'
        s=self.check()['summary']
        for code in ('CROSS_SPLIT_SOURCE_IDENTITY','EXPOSED_TEST_SOURCE','CROSS_SPLIT_SCENE_AXIS'):
            self.assertIn(code,s['declared_constraint_findings'])

    def test_unallocated_byte_alias_still_propagates_scene_axes_and_public_exposure(self):
        self.packet['scenes'].append(copy.deepcopy(self.packet['scenes'][0]))
        self.packet['scenes'][-1]['scene_id']='unallocated-scene'
        self.packet['sources'].append(dict(self.packet['sources'][2],source_id='unallocated',
                                          scene_id='unallocated-scene',exposure='known_public'))
        s=self.check()['summary'];self.assertIn('EXPOSED_TEST_SOURCE',s['declared_constraint_findings'])
        self.assertIn('object_geometry',s['cross_split_overlap_counts_by_axis'])

    def test_unknown_axes_and_unreviewed_asset_records_block_preflight(self):
        self.packet['scenes'][2]['family_axes']['renderer']=None
        self.packet['scenes'][2]['asset_record']['status']='unreviewed'
        codes=self.check()['summary']['declared_constraint_findings']
        self.assertIn('UNRESOLVED_SCENE_FAMILY_AXIS',codes);self.assertIn('UNREVIEWED_SCENE_ASSETS',codes)

    def test_alias_parent_families_are_automatically_inherited_without_false_missing_metadata(self):
        (self.base/'test.bin').write_bytes((self.base/'development.bin').read_bytes())
        (self.base/'child.bin').write_bytes(b'child representation')
        self.packet['sources'].append(dict(self.packet['sources'][0],source_id='child',path='child.bin',
                                          parent_ids=['development'],lineage_status='derived'))
        self.packet['allocations'].append({'allocation_id':'child','split':'development','source_ids':['child'],
                                          'participant_ids':[],'capture_ids':[]})
        s=self.check()['summary'];codes=s['declared_constraint_findings']
        self.assertEqual(s['byte_alias_distinct_scene_groups_n'],1)
        self.assertIn('CROSS_SPLIT_BYTE_IDENTITY',codes)
        self.assertNotIn('MISSING_DECLARED_PARENT_FAMILY',codes)
        self.assertNotIn('BYTE_ALIAS_FAMILY_CONFLICT',codes)

    def test_asset_record_changes_during_audit_are_rejected(self):
        calls=0
        def changing(path):
            nonlocal calls
            if Path(path)==self.base/'assets.json':
                calls+=1
                if calls==2:Path(path).write_bytes(b'changed asset declaration')
            return snapshot_file(path)
        with patch('validation_v03.generated_scene_manifest.snapshot_file',side_effect=changing):
            with self.assertRaisesRegex(ValueError,'Asset record changed'):self.check()

    def test_bad_schema_missing_assets_duplicate_scene_and_cyclic_parents_are_rejected(self):
        original=copy.deepcopy(self.packet)
        for change in ('axis','asset','duplicate','cycle','seed','variant'):
            self.packet=copy.deepcopy(original)
            if change=='axis':self.packet['scenes'][0]['family_axes'].pop('camera')
            if change=='asset':self.packet['scenes'][0]['asset_record']['path']='missing.json'
            if change=='duplicate':self.packet['scenes'][2]['scene_id']='development'
            if change=='cycle':self.packet['sources'][0].update(parent_ids=['development'],lineage_status='derived')
            if change=='seed':self.packet['scenes'][0]['seed']=True
            if change=='variant':self.packet['sources'][0].pop('variant_parameters')
            with self.subTest(change=change),self.assertRaises((ValueError,OSError)):self.check()

    def test_generated_camera_ids_cannot_be_used_to_fabricate_capture_provenance(self):
        packet={'schema_version':1,'data_scope':'synthetic_metadata','source_origin':'generated_3d',
                'require_unexposed_test':True,'sources':[{'source_id':'s','path':'development.bin',
                'parent_ids':[],'family_ids':['f'],'capture_ids':['fake-camera'],
                'lineage_status':'root_of_supplied_material','exposure':'declared_unused'}],
                'allocations':[{'allocation_id':'a','source_ids':['s'],'split':'diagnostic','participant_ids':[],'capture_ids':[]}]}
        with self.assertRaisesRegex(ValueError,'camera'):lineage_audit(packet,base=self.base)

    def test_score_csv_is_bound_and_cli_rejects_overlap_before_threshold_selection(self):
        rows=[];result=self.check()
        for allocation in list(self.packet['allocations']):
            split=allocation['split'];families=';'.join(sorted(result['allocations'][split]['family_ids']))
            rows.append(dict(trial_id=split,split=split,source_family_ids=families,participant_id=split+'-person',
                capture_id=split+'-response',label='human',outcome='scored',legacy_score='.9',candidate_score='.9'))
            attack=dict(rows[-1],trial_id=split+'attack',participant_id='',capture_id=split+'-attack',
                        label='attack',legacy_score='.1',candidate_score='.1');rows.append(attack)
            self.packet['allocations'].append(dict(allocation,allocation_id=attack['trial_id'],participant_ids=[],capture_ids=[attack['capture_id']]))
        result=self.check();validate_score_rows(rows,result)
        bad=copy.deepcopy(rows);bad[0]['source_family_ids']='seed-only'
        with self.assertRaises(ValueError):validate_score_rows(bad,result)
        scores=self.base/'scores.csv';manifest=self.base/'scene.json';output=self.base/'result.json'
        with scores.open('w',newline='',encoding='utf8') as stream:
            writer=csv.DictWriter(stream,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
        manifest.write_text(json.dumps(self.packet))
        args=[sys.executable,'-m','validation_v03.compare_scores','--input',str(scores),'--output',str(output),
              '--generated-scene-manifest',str(manifest),'--min-human-accept','1','--max-attack-accept','0']
        run=subprocess.run(args,capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(output.read_text())['lineage_preflight']['source_origin'],'generated_3d')
        output.unlink();self.packet['scenes'][2]['family_axes']['camera']=self.packet['scenes'][0]['family_axes']['camera']
        manifest.write_text(json.dumps(self.packet));run=subprocess.run(args,capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0);self.assertIn('no thresholds selected',run.stderr);self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
