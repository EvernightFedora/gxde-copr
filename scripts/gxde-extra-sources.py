#!/usr/bin/env python3
"""Pin the remaining GXDE AUR applications to release tags and make SRPM trees."""
import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'packages/gxde-extra'
MANIFEST = json.loads((PACKAGE / 'manifest.json').read_text())

QT6_WIDGET = {'gxde-boot-maker', 'gxde-calendar', 'gxde-dict',
              'gxde-dlna-caster', 'gxde-editor', 'gxde-filetransfer',
              'gxde-font-manager', 'gxde-image-viewer', 'gxde-music',
              'gxde-ocr', 'gxde-picker', 'gxde-system-assistant',
              'gxde-voice-recorder'}

EXTRA_BUILDREQS = {
    'dde-clipboard': ['extra-cmake-modules kf6-kwayland-devel',
                      'cups-devel systemd-devel vulkan-headers wayland-devel'],
    'gxde-boot-maker': ['xcb-util-devel startup-notification-devel'],
    'gxde-calendar': ['libical-devel'],
    'gxde-camera': ['pkgconfig(libavformat) pkgconfig(libavcodec) pkgconfig(libavutil)',
                    'qt6-qtmultimedia-devel pkgconfig(gstreamer-1.0)',
                    'portaudio-devel libusb1-devel libpciaccess-devel'],
    'gxde-clone': ['gxde-file-manager-devel'],
    'gxde-dict': ['qt6-qtmultimedia-devel pkgconfig(x11) pkgconfig(xext) pkgconfig(xtst)'],
    'gxde-dlna-caster': ['qt6-qtwebsockets-devel pkgconfig(libpipewire-0.3)',
                         'pkgconfig(libavformat)'],
    'gxde-editor': ['qt6-qtwebengine-devel qt6-qtwebchannel-devel',
                    'kf6-kcodecs-devel kf6-ksyntaxhighlighting-devel',
                    'polkit-qt6-1-devel pkgconfig(xcb) xcb-util-devel'],
    'gxde-font-manager': ['pkgconfig(fontconfig) pkgconfig(freetype2)'],
    'gxde-image-viewer': ['libexif-devel glib2-devel pkgconfig(x11)',
                          'pkgconfig(xext) freeimage-devel LibRaw-devel'],
    'gxde-log-viewer': ['boost-devel rapidjson-devel libzip-devel minizip-devel',
                        'xerces-c-devel polkit-qt6-1-devel',
                        'gsettings-qt6-devel pkgconfig(zlib)'],
    'gxde-music': ['qt6-qtmultimedia-devel taglib-devel libcue-devel icu-devel',
                   'pkgconfig(libavformat) pkgconfig(libavcodec) pkgconfig(libavutil)',
                   'pkgconfig(x11) pkgconfig(xext)'],
    'gxde-ocr': ['boost-devel eigen3-devel opencv-devel'],
    'gxde-picker': ['pkgconfig(x11) pkgconfig(xext) pkgconfig(xtst)',
                    'pkgconfig(egl) pkgconfig(wayland-client) pkgconfig(xcb)',
                    'xcb-util-devel'],
    'gxde-reader': ['libgxps-devel cairo-devel glib2-devel djvulibre-devel',
                    'libjpeg-turbo-devel lcms2-devel openjpeg2-devel',
                    'libchardet-devel libarchive-devel libtiff-devel',
                    'libpng-devel gtest-devel qt6-qtwebengine-devel',
                    'pkgconfig(zlib) pkgconfig(freetype2)'],
    'gxde-roller': ['kf6-karchive-devel kf6-kcodecs-devel libarchive-devel',
                    'openssl-devel pkgconfig(zlib) libzip-devel minizip-devel',
                    'libsecret-devel poppler-cpp-devel gtest-devel'],
    'gxde-screen-recorder': ['qt6-qtmultimedia-devel pkgconfig(gstreamer-app-1.0)',
                             'pkgconfig(libavformat) pkgconfig(libavcodec)',
                             'pkgconfig(libavutil) pkgconfig(libdrm)',
                             'portaudio-devel libusb1-devel libepoxy-devel',
                             'pkgconfig(x11) pkgconfig(xext) pkgconfig(xtst)',
                             'pkgconfig(xcursor) pkgconfig(xfixes) pkgconfig(xrandr)',
                             'xcb-util-devel'],
    'gxde-system-assistant': ['qt6-qtcharts-devel libqtxdg-devel procps-ng-devel'],
    'gxde-system-monitor': ['polkit-qt6-1-devel icu-devel libcap-devel',
                            'libpcap-devel libnl3-devel pkgconfig(xcb)',
                            'xcb-util-wm-devel'],
    'gxde-voice-recorder': ['qt6-qtmultimedia-devel pkgconfig(libavformat)',
                            'pkgconfig(libavcodec) pkgconfig(libavutil)',
                            'pkgconfig(libavdevice)'],
    'spark-webapp-runtime': ['qt6-qtwebengine-devel'],
}


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = load_script('gxde-core-sources')
sources = load_script('dtk5-sources')


def resolve_one(name, meta, previous):
    repo = meta['repo']
    refs = subprocess.check_output(
        ['git', 'ls-remote', '--tags', f'https://github.com/{repo}.git'],
        text=True, timeout=120)
    tag, commit = core.latest_tag(refs)
    if previous:
        if core.tag_key(tag) < core.tag_key(previous['tag']):
            raise ValueError(f'{name}: release tag rolled back')
        if tag == previous['tag'] and commit != previous['commit']:
            raise ValueError(f'{name}: released tag moved')
    url = f'https://codeload.github.com/{repo}/tar.gz/{commit}'
    filename = f'{meta["upstream"]}-{commit}.tar.gz'
    cache = ROOT / 'build/source-cache' / filename
    digest = sources.download(url, cache, previous['sha256'] if previous and commit == previous['commit'] else None)
    version = core.rpm_version(tag)
    release = (previous.get('release', 1) + 1 if previous and previous['commit'] != commit and
               previous['version'] == version else previous.get('release', 1) if previous and
               previous['commit'] == commit else 1)
    print(f'{name}: {tag} ({commit[:12]})', flush=True)
    return name, {'version': version, 'release': release, 'tag': tag,
                  'commit': commit, 'url': url, 'sha256': digest}


def update(selected):
    path = PACKAGE / 'upstream-lock.json'
    old = json.loads(path.read_text()) if path.exists() else {}
    result = dict(old)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(resolve_one, name, MANIFEST[name], old.get(name)) for name in selected]
        for future in concurrent.futures.as_completed(futures):
            name, value = future.result()
            result[name] = value
    path.write_text(json.dumps(dict(sorted(result.items())), indent=2) + '\n')


def prepare_one(name, lock):
    meta = MANIFEST[name]
    item = lock[name]
    commit = item['commit']
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError(f'{name}: invalid commit')
    output = ROOT / 'build' / f'{name}-rpmbuild'
    for directory in ('SOURCES', 'SPECS', 'BUILD', 'BUILDROOT', 'RPMS', 'SRPMS'):
        (output / directory).mkdir(parents=True, exist_ok=True)
    filename = f'{meta["upstream"]}-{commit}.tar.gz'
    source = output / 'SOURCES' / filename
    cache = ROOT / 'build/source-cache' / filename
    if cache.exists() and hashlib.sha256(cache.read_bytes()).hexdigest() == item['sha256']:
        shutil.copyfile(cache, source)
    sources.download(item['url'], source, item['sha256'])
    checks = [f'{item["sha256"]}  {filename}']
    infra = json.loads((ROOT / 'packages/gxde-infra/upstream-lock.json').read_text())
    tool = infra['components']['deepin-gettext-tools']
    tool_archive = ROOT / 'build/source-cache' / f'deepin-gettext-tools-{tool["commit"]}.tar.gz'
    sources.download(tool['url'], tool_archive, tool['sha256'])
    with tarfile.open(tool_archive) as tar:
        for source_name, output_name in (('src/policy_ts_convert.py', 'deepin-policy-ts-convert'),
                                         ('src/desktop_ts_convert.pl', 'deepin-desktop-ts-convert')):
            member_name = f'deepin-gettext-tools-{tool["commit"]}/{source_name}'
            content = tar.extractfile(member_name).read()
            (output / 'SOURCES' / output_name).write_bytes(content)
            checks.append(f'{hashlib.sha256(content).hexdigest()}  {output_name}')
    (output / 'SOURCES/sources.sha256').write_text('\n'.join(checks) + '\n')
    for file in ('build.sh', 'split-files.py'):
        shutil.copyfile(PACKAGE / file, output / 'SOURCES' / file)
    (output / 'SOURCES/upstream-lock.json').write_text(json.dumps(item, indent=2) + '\n')
    spec = (PACKAGE / 'extra.spec.in').read_text()
    values = {'@NAME@': name, '@VERSION@': item['version'], '@RELEASE@': str(item['release']),
              '@TAG@': item['tag'], '@COMMIT@': commit, '@REPO@': meta['repo'],
              '@UPSTREAM@': meta['upstream'], '@SUMMARY@': meta['summary'],
              '@LICENSE@': meta['license'],
              '@SOURCE@': f'Source0:        {item["url"]}#/{filename}',
              '@BUILDREQS@': build_requires(name, meta),
              '@REQUIRES@': runtime_requires(name, meta),
              '@PROVIDES@': provides(name, meta),
              '@DEBUG@': '%global debug_package %{nil}' if meta['build'] in ('copy', 'make') else '',
              '@ARCH@': 'BuildArch:      noarch' if meta['build'] in ('copy', 'make') else
                       'ExclusiveArch:  x86_64 aarch64'}
    for key, value in values.items():
        spec = spec.replace(key, value)
    (output / 'SPECS' / f'{name}.spec').write_text(spec)


def build_requires(name, meta):
    if meta['build'] == 'copy':
        return 'BuildRequires:  python3'
    if meta['build'] == 'make':
        return 'BuildRequires:  make python3 qt6-qttools-devel qt6-linguist'
    reqs = ['gcc gcc-c++ make pkgconf-pkg-config python3 gettext',
            'qt6-qtbase-devel qt6-qttools-devel qt6-linguist',
            'qt6-qtsvg-devel qt6-qtdeclarative-devel qt6-qt5compat-devel',
            'perl-interpreter perl-XML-LibXML perl-Config-Tiny']
    if meta['build'] == 'cmake':
        reqs.append('cmake ninja-build')
    if name == 'gxde-clone':
        reqs = ['gcc gcc-c++ make cmake ninja-build pkgconf-pkg-config python3 gettext',
                'qt5-qtbase-devel qt5-qttools-devel qt5-linguist qt5-qtsvg-devel',
                'gxde-dtk5-devel gxde-dtk2-devel gxde-dtk2-widget-devel']
    else:
        reqs.append('gxde-dtk6-devel')
        if name in QT6_WIDGET:
            reqs.append('gxde-dtk2-qt6-devel')
    if name in ('dde-clipboard', 'gxde-calendar', 'gxde-roller'):
        reqs.append('gxde-infra-devel')
    if name in ('dde-clipboard', 'gxde-reader', 'gxde-screen-recorder'):
        reqs.append('gxde-core')
    if name in ('gxde-font-manager', 'gxde-reader'):
        reqs.append('gxde-file-manager-devel')
    if name == 'gxde-reader':
        reqs.append('gxde-search-devel')
    if name == 'gxde-system-monitor':
        reqs.append('gxde-dock-devel gxde-app-management-devel')
    reqs += EXTRA_BUILDREQS.get(name, [])
    return '\n'.join('BuildRequires:  ' + part for part in reqs)


def runtime_requires(name, meta):
    if name == 'gxde-downloader-neo':
        return 'Requires:       spark-webapp-runtime aria2 unzip python3 python3-requests bash'
    if name == 'gxde-hardware-viewer':
        return 'Requires:       python3 python3-qt6 python3-psutil python3-dbus pciutils usbutils polkit bash'
    reqs = []
    if name == 'gxde-clone':
        reqs.extend(('gxde-dtk5', 'gxde-dtk2', 'partclone', 'ntfs-3g', 'xfsprogs'))
    else:
        reqs.append('gxde-dtk6')
        if name in QT6_WIDGET:
            reqs.append('gxde-dtk2-qt6')
    if name in ('dde-clipboard', 'gxde-calendar', 'gxde-roller'):
        reqs.append('gxde-infra')
    if name in ('dde-clipboard', 'gxde-reader', 'gxde-screen-recorder'):
        reqs.append('gxde-core')
    if name == 'gxde-system-monitor':
        reqs.append('gxde-app-management')
    return 'Requires:       ' + ' '.join(reqs)


def provides(name, meta):
    aliases = {'dde-clipboard': 'deepin-clipboard', 'gxde-calculator': 'deepin-calculator',
               'gxde-calendar': 'dde-calendar', 'gxde-camera': 'deepin-camera',
               'gxde-clone': 'deepin-clone', 'gxde-font-manager': 'gxde-font-installer',
               'gxde-log-viewer': 'deepin-log-viewer', 'gxde-ocr': 'deepin-ocr',
               'gxde-reader': 'deepin-reader', 'gxde-roller': 'deepin-compressor',
               'gxde-screen-recorder': 'deepin-screen-recorder',
               'gxde-system-monitor': 'deepin-system-monitor',
               'gxde-downloader-neo': 'gxde-downloader'}
    alias = aliases.get(name)
    return f'Provides:       {alias} = %{{version}}-%{{release}}' if alias else ''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('update', 'prepare'))
    parser.add_argument('--package', choices=tuple(MANIFEST) + ('all',), default='all')
    args = parser.parse_args()
    selected = list(MANIFEST) if args.package == 'all' else [args.package]
    if args.command == 'update':
        update(selected)
    else:
        lock = json.loads((PACKAGE / 'upstream-lock.json').read_text())
        for name in selected:
            prepare_one(name, lock)
            print(f'prepared {name}', flush=True)


if __name__ == '__main__':
    main()
