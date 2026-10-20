#!/usr/bin/env python3
"""Lock flakewm (GXDE Wayland compositor) to the latest release tag."""
import importlib.util
import re
import subprocess
from pathlib import Path

spec = importlib.util.spec_from_file_location('dtk_sources', Path(__file__).with_name('dtk5-sources.py'))
sources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sources)

sources.MODULES = ('flakewm',)
sources.CORE_MODULE = 'flakewm'
sources.SPEC_NAME = 'flakewm'
sources.PACKAGE = sources.ROOT / 'packages/flakewm'
sources.DEFAULT_OUTPUT = sources.ROOT / 'build/flakewm-rpmbuild'
UPSTREAM = 'GXDE-OS/flake-wm'

TAG = re.compile(r'v?(\d+(?:\.\d+)*)(?:-?gxde(\d+))?$')


def tag_key(tag):
    match = TAG.fullmatch(tag)
    if not match:
        raise ValueError(f'Unsupported release tag: {tag}')
    numbers = tuple(map(int, match[1].split('.')))
    return numbers + (0,) * (8 - len(numbers)), int(match[2] or 0)


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
    return match[1] + (f'.gxde{match[2]}' if match[2] else '')


def resolve(old, cache):
    components = {}
    for name in sources.MODULES:
        refs = subprocess.check_output(['git', 'ls-remote', '--tags',
                                        f'https://github.com/{UPSTREAM}.git'],
                                       text=True, timeout=120)
        tag, commit = latest_tag(refs)
        previous = old.get('components', {}).get(name)
        if previous and tag_key(tag) < tag_key(previous['tag']):
            raise ValueError(f'{name}: upstream tag rollback requires manual review')
        if previous and previous['tag'] == tag and previous['commit'] != commit:
            raise ValueError(f'{name}: released tag moved; refusing automatic update')
        url = f'https://codeload.github.com/{UPSTREAM}/tar.gz/{commit}'
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


def prepare(lock, destination):
    import hashlib
    import shutil
    ROOT = sources.ROOT
    PACKAGE = sources.PACKAGE

    for directory in ("SOURCES", "SPECS", "BUILD", "BUILDROOT", "RPMS", "SRPMS"):
        (destination / directory).mkdir(parents=True, exist_ok=True)

    definitions, sources_list, checks = [], [], []
    for index, name in enumerate(sources.MODULES):
        component = lock["components"][name]
        commit = component["commit"]
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValueError(f"Invalid commit for {name}")
        filename = f"{name}-{commit}.tar.gz"
        cached = ROOT / "build/source-cache" / filename
        if cached.exists() and hashlib.sha256(cached.read_bytes()).hexdigest() == component["sha256"]:
            shutil.copyfile(cached, destination / "SOURCES" / filename)
        sources.download(component["url"], destination / "SOURCES" / filename, component["sha256"])
        definitions.append(f"%global commit{index} {commit}")
        sources_list.append(f"Source{index}: {component['url']}#/{filename}")
        checks.append(f"{component['sha256']}  {filename}")

    template = (PACKAGE / "flakewm.spec.in").read_text()
    replacements = {
        "@VERSION@": lock["version"],
        "@RELEASE@": str(lock["release"]),
        "@COMMITS@": "\n".join(definitions),
        "@SOURCES@": "\n".join(sources_list),
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    (destination / "SPECS/flakewm.spec").write_text(template)
    (destination / "SOURCES/sources.sha256").write_text("\n".join(checks) + "\n")
    for name in ("build.sh", "split-files.py"):
        shutil.copyfile(PACKAGE / name, destination / "SOURCES" / name)
    shutil.copyfile(PACKAGE / "upstream-lock.json", destination / "SOURCES/upstream-lock.json")


sources.prepare = prepare

if __name__ == '__main__':
    sources.main()
