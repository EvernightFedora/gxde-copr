#!/usr/bin/env python3
"""Generate exact RPM file lists for the GXDE core runtime and SDK."""
from pathlib import Path
import sys


def category(path, libdir):
    # Only .so symlinks directly in libdir are development files; plugin .so
    # files in subdirectories (gtk-3.0/modules, qt6/plugins, gxde-dock/plugins,
    # ...) are runtime payloads.
    parent = path.rsplit('/', 1)[0]
    if (path.startswith('/usr/include/') or path.startswith('/usr/share/cmake/')
            or path.startswith('/usr/share/pkgconfig/')
            or path.startswith(f'{libdir}/cmake/') or path.startswith(f'{libdir}/pkgconfig/')
            or path.endswith(('.a', '.prl'))
            or (parent == libdir and path.endswith('.so'))):
        return 'devel'
    return 'runtime'


def main():
    root, libdir = map(Path, sys.argv[1:])
    common = {'/etc', '/etc/xdg', '/etc/xdg/autostart', '/etc/dbus-1', '/etc/fonts',
              '/usr', '/usr/bin', '/usr/lib', '/usr/lib64', '/usr/libexec',
              '/usr/share', '/usr/share/applications', '/usr/share/dbus-1',
              '/usr/share/dbus-1/services', '/usr/share/dbus-1/system-services',
              '/usr/share/dbus-1/system.d', '/usr/share/polkit-1',
              '/usr/share/polkit-1/actions', '/usr/share/polkit-1/rules.d',
              '/usr/share/glib-2.0', '/usr/share/glib-2.0/schemas',
              '/usr/share/gtk-3.0', '/usr/share/icons', '/usr/share/icons/hicolor',
              '/usr/share/locale', '/usr/share/wallpapers',
              '/usr/share/gxde-daemon', '/usr/share/gxde-daemon/dock/translations',
              '/usr/share/gxde-daemon/daemon-k9-conf', '/usr/share/gxde-daemon/plugins',
              '/usr/share/gxde-k9', '/usr/share/gxde-k9/system', '/usr/share/gxde-k9/edging',
              '/usr/share/gxde-default-settings',
              '/usr/share/systemd', '/usr/lib/systemd', '/usr/lib/systemd/system',
              '/usr/lib/systemd/user', '/usr/share/systemd/user',
              '/usr/share/wayland-sessions', '/usr/share/wayland-protocols',
              '/usr/share/xdg-desktop-portal', '/usr/share/xdg-desktop-portal/portals',
              '/var', '/var/lib', '/var/lib/AccountsService',
              '/var/lib/AccountsService/icons', '/var/cache', '/var/cache/image-blur',
              # Owned by polkit-pkla-compat (a daemon-group Requires); ship the
              # .pkla files inside without claiming the directories.
              '/var/lib/polkit-1', '/var/lib/polkit-1/localauthority',
              '/var/lib/polkit-1/localauthority/10-vendor.d',
              '/usr/include', '/usr/include/gxde-dock',
              str(libdir), f'{libdir}/cmake', f'{libdir}/pkgconfig',
              f'{libdir}/gxde-dock', f'{libdir}/qt5/plugins',
              f'{libdir}/qt6/plugins', f'{libdir}/qt6/qml'}
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
            if name == 'devel':
                # Split packages without a development surface ship no
                # devel.files; their specs declare no devel subpackage.
                continue
            raise ValueError(f'Empty RPM package: {name}')
        Path(f'{name}.files').write_text('\n'.join(paths) + '\n')


if __name__ == '__main__':
    main()
