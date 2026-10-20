#!/usr/bin/env python3
"""Generate exact RPM file lists for the infrastructure runtime and SDK."""
from pathlib import Path
import sys


def category(path, libdir):
    if (path.startswith('/usr/include/') or path.startswith('/usr/share/gocode')
            or path.startswith('/usr/share/treeland-protocols/')
            or path.startswith('/usr/share/cmake/')
            or path.startswith('/usr/share/pkgconfig/')
            or path.startswith(f'{libdir}/cmake/') or path.startswith(f'{libdir}/pkgconfig/')
            or path.endswith(('.a', '.prl'))
            or (path.startswith(libdir + '/') and path.endswith('.so'))):
        return 'devel'
    return 'runtime'


def main():
    root, libdir = map(Path, sys.argv[1:])
    common = {'/etc', '/etc/xdg', '/etc/xdg/autostart', '/usr', '/usr/bin', '/usr/lib',
              '/usr/lib64', '/usr/libexec', '/usr/share', '/usr/include',
              '/usr/share/applications', '/usr/share/icons', '/usr/share/icons/hicolor',
              '/usr/share/glib-2.0', '/usr/share/glib-2.0/schemas', '/usr/share/dbus-1',
              '/usr/share/dbus-1/services', '/usr/share/dbus-1/system-services',
              '/usr/share/polkit-1', '/usr/share/polkit-1/actions', '/usr/share/polkit-1/rules.d',
              '/usr/share/systemd', '/usr/lib/systemd', '/usr/lib/systemd/system',
              '/usr/lib/systemd/user', '/usr/lib/tmpfiles.d', '/var', '/var/lib',
              # Fedora polkit-pkla-compat owns these directories with its
              # required root:polkitd permissions. Only ship our .pkla file.
              '/var/lib/polkit-1', '/var/lib/polkit-1/localauthority',
              '/var/lib/polkit-1/localauthority/10-vendor.d',
              str(libdir), f'{libdir}/cmake', f'{libdir}/pkgconfig'}
    groups = {'runtime': [], 'devel': []}
    for file in sorted(root.rglob('*')):
        path = '/' + file.relative_to(root).as_posix()
        if file.is_dir() and not file.is_symlink() and path in common:
            continue
        if any(char in path for char in ('"', '\n', '%')):
            raise ValueError(f'Unsupported RPM path: {path!r}')
        manifest = ('%dir ' if file.is_dir() and not file.is_symlink() else '') + f'"{path}"'
        if path.startswith('/etc/') and file.is_file() and not file.is_symlink():
            manifest = '%config(noreplace) ' + manifest
        groups[category(path, str(libdir))].append(manifest)
    for name, paths in groups.items():
        if not paths:
            raise ValueError(f'Empty RPM package: {name}')
        Path(f'{name}.files').write_text('\n'.join(paths) + '\n')


if __name__ == '__main__':
    main()
