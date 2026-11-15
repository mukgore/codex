import os
from pathlib import Path
import tempfile
import unittest
from validation_v03.private_paths import inside_repository


class PrivatePathTests(unittest.TestCase):
    def test_nested_and_output_root_markers_remain_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);repo=root/'repo';repo.mkdir();marker=repo/'.git';marker.mkdir()
            self.assertTrue(inside_repository(repo))
            self.assertTrue(inside_repository(repo/'private_artifacts'/'out'))
            marker.rmdir();marker.write_text('gitdir: /elsewhere')
            self.assertTrue(inside_repository(repo/'out'))
            marker.unlink();marker.symlink_to(root/'missing')
            self.assertTrue(inside_repository(repo/'out'))

    def test_cloud_guards_are_empty_readonly_exact_anchor_exceptions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            # Outside a checkout even when a managed Cloud anchor is an ancestor.
            self.assertFalse(inside_repository(root/'private_artifacts'/'new'))
            (root/'.git').mkdir();(root/'.git').chmod(0o555)
            self.assertTrue(inside_repository(root/'out'))
            (root/'.git').chmod(0o755)
