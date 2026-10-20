#!/usr/bin/env python3
"""Generate exact file ownership for one GXDE extra application."""
from pathlib import Path
import sys


COMMON = {'/etc', '/etc/xdg', '/usr', '/usr/bin', '/usr/lib', '/usr/lib64',
          '/usr/libexec', '/usr/share', '/usr/share/applications',
          '/usr/share/icons', '/usr/share/icons/hicolor', '/usr/share/locale',
          '/usr/share/doc', '/usr/share/licenses', '/usr/share/glib-2.0',
          '/usr/share/glib-2.0/schemas', '/usr/share/dbus-1',
          '/usr/share/dbus-1/services', '/usr/share/polkit-1',
          '/usr/share/polkit-1/actions', '/usr/share/metainfo',
          '/usr/share/mime', '/usr/share/mime/packages',
          '/usr/share/xdg-desktop-portal', '/usr/share/systemd',
          '/usr/lib/systemd', '/usr/lib/systemd/system'}


def main():
    root = Path(sys.argv[1])
    paths = []
    for item in sorted(root.rglob('*')):
        path = '/' + item.relative_to(root).as_posix()
        if path.startswith('/usr/src/debug/'):
            continue
        if item.is_dir() and not item.is_symlink() and path in COMMON:
            continue
        if any(char in path for char in ('"', '\n', '%')):
            raise ValueError(f'Unsupported RPM path: {path!r}')
        prefix = '%dir ' if item.is_dir() and not item.is_symlink() else ''
        if path.startswith('/etc/') and item.is_file() and not item.is_symlink():
            prefix = '%config(noreplace) ' + prefix
        paths.append(prefix + f'"{path}"')
    if not paths:
        raise ValueError('Application installed no files')
    Path('runtime.files').write_text('\n'.join(paths) + '\n')


if __name__ == '__main__':
    main()
