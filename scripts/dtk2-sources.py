#!/usr/bin/env python3
"""Prepare DTK2 from pinned, checksummed upstream release tags."""
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('dtk_sources', Path(__file__).with_name('dtk5-sources.py'))
sources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sources)
sources.MODULES = ('dde-qt-dbus-factory', 'dtk2widget', 'gxde-qt5integration')
sources.CORE_MODULE = 'dtk2widget'
sources.SPEC_NAME = 'gxde-dtk2'
sources.PACKAGE = sources.ROOT / 'packages/gxde-dtk2'
sources.DEFAULT_OUTPUT = sources.ROOT / 'build/dtk2-rpmbuild'
if __name__ == '__main__':
    sources.main()
