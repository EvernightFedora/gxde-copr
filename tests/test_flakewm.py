import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_dtk5 import load

flakewm = load('flakewm_sources', 'scripts/flakewm-sources.py')


class Tags(unittest.TestCase):
    def test_gxde_suffix_preferred(self):
        refs = ('a refs/tags/3.0.0-gxde2\n'
                'b refs/tags/3.0.0-gxde2^{}\n'
                'c refs/tags/3.0.1-gxde1\n'
                'd refs/tags/3.0.1-gxde1^{}\n')
        self.assertEqual(flakewm.latest_tag(refs), ('3.0.1-gxde1', 'd'))

    def test_rpm_version(self):
        self.assertEqual(flakewm.rpm_version('3.0.1-gxde1'), '3.0.1.gxde1')
        self.assertEqual(flakewm.rpm_version('3.0.0'), '3.0.0')

    def test_no_head_fallback(self):
        with self.assertRaises(ValueError):
            flakewm.latest_tag('a refs/heads/main')

    def test_moved_tag_rejected(self):
        old = {"components": {"flakewm": {"tag": "3.0.1-gxde1", "commit": "old"}}}
        with patch.object(flakewm.sources.subprocess, "check_output",
                          return_value="new refs/tags/3.0.1-gxde1"):
            with self.assertRaisesRegex(ValueError, "moved"):
                flakewm.resolve(old, Path("unused"))

    def test_rollback_rejected(self):
        old = {"components": {"flakewm": {"tag": "3.0.1-gxde1", "commit": "old"}}}
        with patch.object(flakewm.sources.subprocess, "check_output",
                          return_value="new refs/tags/2.0.0-gxde1"):
            with self.assertRaisesRegex(ValueError, "rollback"):
                flakewm.resolve(old, Path("unused"))

    def test_single_module(self):
        self.assertEqual(len(flakewm.sources.MODULES), 1)
        self.assertEqual(flakewm.sources.MODULES[0], 'flakewm')


class Prepare(unittest.TestCase):
    def test_lock_has_one_component(self):
        lock = json.loads((flakewm.sources.PACKAGE / 'upstream-lock.json').read_text())
        self.assertEqual(len(lock['components']), 1)
        self.assertIn('flakewm', lock['components'])

    def test_prepared_spec_has_sources(self):
        lock = json.loads((flakewm.sources.PACKAGE / 'upstream-lock.json').read_text())
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(flakewm.sources, 'download'):
            flakewm.prepare(lock, Path(tmp))
            spec = (Path(tmp) / 'SPECS/flakewm.spec').read_text()
            self.assertIn(f'Version:        {lock["version"]}', spec)
            self.assertIn('Source0:', spec)
            self.assertIn('%global commit0', spec)
            self.assertTrue((Path(tmp) / 'SOURCES/sources.sha256').exists())
            self.assertTrue((Path(tmp) / 'SOURCES/build.sh').exists())


if __name__ == '__main__':
    unittest.main()
