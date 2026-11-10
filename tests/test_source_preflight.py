import tempfile
import unittest
from pathlib import Path

from validation_v03.source_preflight import audit


class SourcePreflightTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.rows = []
        for index, split in enumerate(('development', 'validation', 'test')):
            asset = f'asset{index}'
            self.rows.append(dict(asset_id=asset, source_family_id=f'family{index}',
                                  capture_id=f'capture{index}', performer_id=f'performer{index}',
                                  path=f'{asset}.bin', split=split, parent_asset_ids=[]))
            (self.root / self.rows[-1]['path']).write_bytes(bytes([index]))

    def test_valid_single_parent_variant_stays_with_root(self):
        child = dict(self.rows[0], asset_id='masked', parent_asset_ids=['asset0'])
        self.assertEqual(audit(self.rows + [child], self.root)['status'], 'PASS')

    def test_relabelled_copy_and_parent_in_test_blocked(self):
        self.rows[2]['path'] = self.rows[0]['path']
        self.rows[2]['parent_asset_ids'] = ['asset0']
        report = audit(self.rows, self.root)
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertEqual(report['findings'], {'cross_split_sha256_groups': 1,
                         'cross_split_parent_edges': 1, 'inconsistent_parent_lineage_edges': 1})
        self.assertNotIn('asset0', str(report))

    def test_cross_split_performer_and_capture(self):
        for field in ('capture_id', 'performer_id', 'source_family_id'):
            self.rows[1][field] = self.rows[0][field]
        findings = audit(self.rows, self.root)['findings']
        self.assertEqual(len(findings), 3)
        self.assertTrue(all(value == 1 for value in findings.values()))

    def test_missing_parent_cycle_and_split(self):
        self.rows[0]['parent_asset_ids'] = ['asset0']
        self.rows[1]['parent_asset_ids'] = ['missing']
        findings = audit(self.rows[:2], self.root)['findings']
        self.assertEqual(findings, {'missing_parent_edges': 1,
                                    'lineage_cycle_detected': 1, 'missing_splits': 1})

    def test_outside_root_fails(self):
        self.rows[0]['path'] = '../outside.bin'
        with self.assertRaises(ValueError):
            audit(self.rows, self.root)
