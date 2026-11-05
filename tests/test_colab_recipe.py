import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

path=Path(__file__).resolve().parents[1]/'tools'/'prepare_hamer_colab.py'
spec=importlib.util.spec_from_file_location('prepare_hamer_colab',path);recipe=importlib.util.module_from_spec(spec);spec.loader.exec_module(recipe)


class ColabRecipeTests(unittest.TestCase):
    def test_only_dedicated_content_roots_are_accepted(self):
        self.assertEqual(str(recipe.root_name('/content/handcaptcha_hamer_core')),'/content/handcaptcha_hamer_core')
        for value in ('/content','/content/drive','/content/handcaptcha_a/../drive','/etc/handcaptcha_core','relative','/content/handcaptcha_a/b'):
            with self.assertRaises(ValueError):recipe.root_name(value)

    def test_recipe_cannot_run_on_this_windows_pc(self):
        with patch.object(recipe.platform,'system',return_value='Windows'):
            with self.assertRaises(ValueError):recipe.run('/content/handcaptcha_hamer_core')
