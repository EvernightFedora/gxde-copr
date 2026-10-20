#!/usr/bin/env python3
"""Prepare DTK6 using the shared release-tag and checksum policy."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("dtk_sources", Path(__file__).with_name("dtk5-sources.py"))
sources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sources)
sources.MODULES = ("dtk6log", "dtk6core", "dtk6gui", "dtk6widget",
                   "dtk6declarative", "dde-qt6platform-plugins", "qt6integration")
sources.CORE_MODULE = "dtk6core"
sources.SPEC_NAME = "gxde-dtk6"
sources.PACKAGE = sources.ROOT / "packages/gxde-dtk6"
sources.DEFAULT_OUTPUT = sources.ROOT / "build/dtk6-rpmbuild"

if __name__ == "__main__":
    sources.main()
