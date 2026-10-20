#!/usr/bin/env python3
"""Keep Qt6 plugins and QML modules in runtime; split only SDK files."""
import sys
from pathlib import Path


def category(path, libdir):
    if (path.startswith('/usr/include/') or path.startswith(f'{libdir}/cmake/')
            or path.startswith(f'{libdir}/pkgconfig/') or '/mkspecs/' in path
            or path in {f'{libdir}/libdtk6{x}.so' for x in ('log', 'core', 'gui', 'widget', 'declarative')}):
        return 'devel'
    return 'runtime'


def main():
    root, libdir, qtarchdata = sys.argv[1:]
    root = Path(root)
    shared = {'/usr', '/usr/bin', '/usr/lib', '/usr/lib64', '/usr/libexec', '/usr/include',
              '/usr/share', '/usr/share/qtcreator', '/usr/share/qtcreator/templates',
              '/usr/share/qtcreator/templates/wizards', '/usr/share/qtcreator/templates/wizards/projects',
              libdir, f'{libdir}/cmake', f'{libdir}/pkgconfig', qtarchdata,
              f'{qtarchdata}/mkspecs', f'{qtarchdata}/mkspecs/modules', f'{qtarchdata}/mkspecs/features',
              f'{libdir}/qt6', f'{libdir}/qt6/plugins', f'{libdir}/qt6/qml'}
    groups = {'runtime': [], 'devel': []}
    for file in sorted(root.rglob('*')):
        path = '/' + file.relative_to(root).as_posix()
        is_dir = file.is_dir() and not file.is_symlink()
        if is_dir and path in shared:
            continue
        if any(char in path for char in ('"', '\n', '%')):
            raise ValueError(f'Unsupported RPM filename: {path!r}')
        groups[category(path, libdir)].append(('%dir ' if is_dir else '') + f'"{path}"')
    for key, paths in groups.items():
        if not paths:
            raise ValueError(f'Empty package: {key}')
        Path(f'{key}.files').write_text('\n'.join(paths) + '\n')


if __name__ == '__main__':
    main()
