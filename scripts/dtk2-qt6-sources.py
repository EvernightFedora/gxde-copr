#!/usr/bin/env python3
"""Prepare the tagged Qt6 port of DTK2 Widget and its style plugin."""
import importlib.util
import re
from pathlib import Path

spec = importlib.util.spec_from_file_location('dtk_sources', Path(__file__).with_name('dtk5-sources.py'))
sources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sources)

sources.MODULES = ('dtk2widget-qt6', 'gxde-qt6-integration')
sources.CORE_MODULE = 'dtk2widget-qt6'
sources.SPEC_NAME = 'gxde-dtk2-qt6'
sources.PACKAGE = sources.ROOT / 'packages/gxde-dtk2-qt6'
sources.DEFAULT_OUTPUT = sources.ROOT / 'build/dtk2-qt6-rpmbuild'

arch_tag = re.compile(r'(\d+(?:\.\d+)*)-arch(\d+)$')
base_tag_key = sources.tag_key


def tag_key(tag):
    match = arch_tag.fullmatch(tag)
    if match:
        numbers = tuple(map(int, match[1].split('.')))
        return numbers + (0,) * (8 - len(numbers)), 1, int(match[2])
    numbers, suffix = base_tag_key(tag)
    return numbers, 0, suffix


def latest_tag(refs):
    tags, peeled = {}, {}
    for line in refs.splitlines():
        sha, ref = line.split()
        name = ref.removeprefix('refs/tags/')
        if name.endswith('^{}'):
            peeled[name[:-3]] = sha
        elif sources.TAG.fullmatch(name) or arch_tag.fullmatch(name):
            tags[name] = sha
    if not tags:
        raise ValueError('No stable numeric release tags found; refusing a HEAD fallback')
    tag = max(tags, key=lambda name: (tag_key(name), name))
    return tag, peeled.get(tag, tags[tag])


sources.tag_key = tag_key
sources.latest_tag = latest_tag

if __name__ == '__main__':
    sources.main()
