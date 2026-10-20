#!/usr/bin/env python3
"""Lock GXDE infra to release tags (or an explicit branch for untagged keyring)."""
import importlib.util
import re
import shutil
import subprocess
from pathlib import Path

spec = importlib.util.spec_from_file_location('dtk_sources', Path(__file__).with_name('dtk5-sources.py'))
sources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sources)

sources.MODULES = (
    'golang-gxde-dev', 'gxde-k9', 'disomaster-qt6', 'gxde-api',
    'deepin-keyring', 'libgnome-keyring', 'gxde-desktop-base',
    'gxde-desktop-schemas', 'dframework-dbus-qt6',
    'gxde-network-utils-qt6', 'udisks2-qt6', 'gxde-movie-reborn',
    'libdbusmenu-qt6', 'treeland-protocols', 'xdg-desktop-portal-gxde',
    'deepin-gettext-tools',
)
sources.CORE_MODULE = 'gxde-desktop-base'
sources.SPEC_NAME = 'gxde-infra'
sources.PACKAGE = sources.ROOT / 'packages/gxde-infra'
sources.DEFAULT_OUTPUT = sources.ROOT / 'build/infra-rpmbuild'

TAG = re.compile(r'v?(\d+(?:\.\d+)*(?:\+\d+(?:\.\d+)*)?)(?:(?:-?gxde(\d+))|(?:-arch(\d+))|(?:-(\d+)))?$')
UNTAGGED = {'deepin-keyring': 'master'}


def tag_key(tag):
    match = TAG.fullmatch(tag)
    if not match:
        raise ValueError(f'Unsupported release tag: {tag}')
    numbers = tuple(map(int, re.findall(r'\d+', match[1])))
    kind = 3 if match[3] else 2 if match[2] else 1 if match[4] else 0
    return numbers + (0,) * (10 - len(numbers)), kind, int(match[3] or match[2] or match[4] or 0)


def latest_tag(refs):
    tags, peeled = {}, {}
    for line in refs.splitlines():
        sha, ref = line.split()
        if not ref.startswith('refs/tags/'):
            continue
        name = ref.removeprefix('refs/tags/')
        if name.endswith('^{}'):
            peeled[name[:-3]] = sha
        elif TAG.fullmatch(name):
            tags[name] = sha
    if not tags:
        raise ValueError('No stable numeric release tags found; refusing a HEAD fallback')
    tag = max(tags, key=lambda value: (tag_key(value), value))
    return tag, peeled.get(tag, tags[tag])


def rpm_version(tag):
    match = TAG.fullmatch(tag)
    if not match:
        raise ValueError(f'Unsupported release tag: {tag}')
    suffix = match[2] or match[3] or match[4]
    return match[1].replace('+', '.') + (f'.gxde{suffix}' if match[2] else f'.{suffix}' if suffix else '')


def resolve(old, cache):
    components = {}
    for name in sources.MODULES:
        owner = 'linuxdeepin' if name == 'treeland-protocols' else 'GXDE-OS'
        repo = f'https://github.com/{owner}/{name}.git'
        refs = subprocess.check_output(['git', 'ls-remote', '--tags', '--heads', repo], text=True, timeout=120)
        if name in UNTAGGED:
            branch = UNTAGGED[name]
            commit = next((line.split()[0] for line in refs.splitlines()
                           if line.endswith(f'refs/heads/{branch}')), None)
            if not commit:
                raise ValueError(f'{name}: missing pinned branch {branch}')
            tag = f'branch:{branch}'
        else:
            tag, commit = latest_tag(refs)
        previous = old.get('components', {}).get(name)
        if previous and name not in UNTAGGED and tag_key(tag) < tag_key(previous['tag']):
            raise ValueError(f'{name}: upstream tag rollback requires manual review')
        if previous and previous['tag'] == tag and previous['commit'] != commit and name not in UNTAGGED:
            raise ValueError(f'{name}: released tag moved; refusing automatic update')
        url = f'https://codeload.github.com/{owner}/{name}/tar.gz/{commit}'
        item = {'tag': tag, 'commit': commit, 'url': url}
        item['sha256'] = sources.download(url, cache / f'{name}-{commit}.tar.gz',
                                          previous['sha256'] if previous and previous['commit'] == commit else None)
        components[name] = item
        print(f'{name}: {tag} ({commit[:12]})', flush=True)
    version = rpm_version(components[sources.CORE_MODULE]['tag'])
    changed = components != old.get('components')
    release = old.get('release', 0) + int(changed) if version == old.get('version') else 1
    return {'version': version, 'release': release, 'components': components}


sources.tag_key = tag_key
sources.latest_tag = latest_tag
sources.rpm_version = rpm_version
sources.resolve = resolve

base_prepare = sources.prepare


def prepare(lock, destination):
    base_prepare(lock, destination)
    shutil.copyfile(sources.PACKAGE / 'gxde-k9.tmpfiles.conf',
                    destination / 'SOURCES/gxde-k9.tmpfiles.conf')


sources.prepare = prepare

if __name__ == '__main__':
    sources.main()
