import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_dtk5 import load, sources as dtk5

sources = load('dtk6', 'scripts/dtk6-sources.py').sources
split = load('split6', 'packages/gxde-dtk6/split-files.py')


class DTK6(unittest.TestCase):
    def test_non_core_update_keeps_core_version(self):
        old = json.loads((sources.PACKAGE / 'upstream-lock.json').read_text())
        refs = [f'{old["components"][name]["commit"]} refs/tags/{old["components"][name]["tag"]}' for name in sources.MODULES]
        old['components']['dtk6log']['tag'] = '0.0.5'
        refs[0] = 'a refs/tags/0.0.6-1'
        with patch.object(sources.subprocess, 'check_output', side_effect=refs), patch.object(sources, 'download', return_value='digest'):
            result = sources.resolve(old, Path('unused'))
        self.assertEqual(result['version'], old['version'])
        self.assertEqual(result['release'], old['release'] + 1)
        self.assertEqual(dtk5.CORE_MODULE, 'dtk5core')

    def test_prepare_does_not_require_dtk5common(self):
        lock = json.loads((sources.PACKAGE / 'upstream-lock.json').read_text())
        with tempfile.TemporaryDirectory() as tmp, patch.object(sources, 'download'):
            sources.prepare(lock, Path(tmp))
            spec = (Path(tmp) / 'SPECS/gxde-dtk6.spec').read_text()
            self.assertNotIn('@VERSION@', spec)
            self.assertNotIn('Patch0:', spec)
            self.assertIn('Name:           gxde-dtk6', spec)

    def test_qml_plugin_stays_in_runtime(self):
        self.assertEqual(split.category('/usr/lib64/qt6/qml/org/deepin/dtk/libdtkdeclarativeplugin.so', '/usr/lib64'), 'runtime')
        self.assertEqual(split.category('/usr/lib64/qt6/plugins/platforms/libqdxcb.so', '/usr/lib64'), 'runtime')
        self.assertEqual(split.category('/usr/lib64/libdtk6widget.so', '/usr/lib64'), 'devel')
        self.assertEqual(split.category('/usr/lib64/libdtk6widget.so.6', '/usr/lib64'), 'runtime')
