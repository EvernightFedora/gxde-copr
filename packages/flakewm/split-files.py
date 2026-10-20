#!/usr/bin/env python3
"""Generate the RPM file list for flakewm."""
from pathlib import Path
import sys


def main():
    root = Path(sys.argv[1])
    runtime = []
    for file in sorted(root.rglob('*')):
        path = '/' + file.relative_to(root).as_posix()
        # Skip debuginfo sources — handled by rpm automatically.
        if path.startswith('/usr/src/debug/'):
            continue
        if any(char in path for char in ('"', '\n', '%')):
            raise ValueError(f'Unsupported RPM path: {path!r}')
        if file.is_dir() and not file.is_symlink():
            # Skip common auto-created dirs.
            if path in ('/etc', '/etc/flakewm', '/usr', '/usr/bin', '/usr/lib',
                        '/usr/lib64', '/usr/share', '/usr/share/flakewm',
                        '/usr/share/flakewm/multitask', '/usr/share/doc',
                        '/usr/share/doc/flakewm', '/usr/share/glib-2.0',
                        '/usr/share/glib-2.0/schemas', '/usr/share/licenses',
                        '/usr/share/licenses/flakewm', '/usr/share/locale',
                        '/usr/share/wayland-sessions', '/usr/include',
                        '/usr/include/flakewm', '/usr/lib/udev',
                        '/usr/lib/udev/rules.d', '/usr/lib64/pkgconfig'):
                continue
            manifest = f'%dir "{path}"'
        else:
            manifest = f'"{path}"'
            if path.startswith('/etc/'):
                manifest = '%config(noreplace) ' + manifest
        runtime.append(manifest)
    if not runtime:
        raise ValueError('Empty RPM package: runtime')
    Path('runtime.files').write_text('\n'.join(runtime) + '\n')


if __name__ == '__main__':
    main()
