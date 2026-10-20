#!/usr/bin/env python3
"""Separate Qt6 DTK2 runtime from SDK metadata and linker files."""
import sys
from pathlib import Path


def category(path, libdir, qtarchdata):
    if (path.startswith('/usr/include/') or path.startswith(f'{libdir}/cmake/')
            or path.startswith(f'{libdir}/pkgconfig/') or '/mkspecs/' in path
            or path == f'{libdir}/libdtk2widget.so'):
        return 'devel'
    return 'runtime'


def main():
    root, libdir, qtarchdata = sys.argv[1:]
    root = Path(root)
    shared = {'/usr', '/usr/bin', '/usr/lib', '/usr/lib64', '/usr/include',
              '/usr/share', libdir, f'{libdir}/cmake', f'{libdir}/pkgconfig',
              qtarchdata, f'{qtarchdata}/mkspecs', f'{qtarchdata}/mkspecs/modules',
              f'{libdir}/qt6', f'{libdir}/qt6/plugins'}
    groups = {'runtime': [], 'devel': []}
    for file in sorted(root.rglob('*')):
        path = '/' + file.relative_to(root).as_posix()
        is_dir = file.is_dir() and not file.is_symlink()
        if is_dir and path in shared:
            continue
        if any(c in path for c in ('"', '\n', '%')):
            raise ValueError(f'Unsupported RPM filename: {path!r}')
        groups[category(path, libdir, qtarchdata)].append(('%dir ' if is_dir else '') + f'"{path}"')
    for key, paths in groups.items():
        if not paths:
            raise ValueError(f'Empty {key} package')
        Path(f'{key}.files').write_text('\n'.join(paths) + '\n')


if __name__ == '__main__':
    main()
