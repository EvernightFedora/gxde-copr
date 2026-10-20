import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from test_dtk5 import load

sources = load('dtk2', 'scripts/dtk2-sources.py').sources
split = load('split2', 'packages/gxde-dtk2/split-files.py')


class DTK2(unittest.TestCase):
    def test_release_selection(self):
        self.assertGreater(sources.tag_key('2.5-gxde2'), sources.tag_key('2.5-gxde1'))
        self.assertEqual(sources.rpm_version('2.5-gxde2'), '2.5.gxde2')
        self.assertEqual(sources.latest_tag('a refs/tags/2.5-gxde1\nb refs/tags/2.5-gxde2'), ('2.5-gxde2', 'b'))

    def test_split_widget_sdk(self):
        libdir = '/usr/lib64'
        qtdata = '/usr/lib64/qt5'
        self.assertEqual(split.category('/usr/include/dtk5/DWidget/DApplication', libdir, qtdata), 'widget-devel')
        self.assertEqual(split.category('/usr/lib64/libdtkwidget.so', libdir, qtdata), 'widget-devel')
        self.assertEqual(split.category('/usr/lib64/libdtkwidget.so.2', libdir, qtdata), 'runtime')
        self.assertEqual(split.category('/usr/lib64/pkgconfig/dframeworkdbus.pc', libdir, qtdata), 'devel')
        self.assertEqual(split.category('/usr/lib64/qt5/plugins/styles/libdstyleplugin.so', libdir, qtdata), 'runtime')

    def test_prepared_spec_has_no_patch(self):
        lock = json.loads((sources.PACKAGE / 'upstream-lock.json').read_text())
        with tempfile.TemporaryDirectory() as tmp, patch.object(sources, 'download'):
            sources.prepare(lock, Path(tmp))
            spec = (Path(tmp) / 'SPECS/gxde-dtk2.spec').read_text()
            self.assertIn('Patch0:         0001-factory-python-glob.patch', spec)
            self.assertIn('Name:           gxde-dtk2', spec)
