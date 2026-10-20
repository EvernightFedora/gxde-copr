#!/usr/bin/env python3
"""Split the installed tree without overlapping ownership or hiding new files."""
import sys
from pathlib import Path


def category(path, libdir, qtarchdata):
    widget = ("/usr/include/dtk5/DWidget", f"{libdir}/cmake/DtkWidget")
    if any(path == prefix or path.startswith(prefix + "/") for prefix in widget):
        return "widget-devel"
    if path in (f"{libdir}/libdtkwidget.so", f"{libdir}/pkgconfig/dtkwidget.pc",
                f"{qtarchdata}/mkspecs/modules/qt_lib_DtkWidget.pri"):
        return "widget-devel"
    if (path.startswith("/usr/include/") or path.startswith(f"{libdir}/cmake/")
            or path.startswith(f"{libdir}/pkgconfig/") or "/mkspecs/" in path
            or path in (f"{libdir}/libdtkcore.so", f"{libdir}/libdtkgui.so", f"{libdir}/libdtklog.so")):
        return "devel"
    return "runtime"


def main():
    root, libdir, qtarchdata = sys.argv[1:]
    root = Path(root)
    shared = {"/usr", "/usr/bin", "/usr/lib", "/usr/lib64", "/usr/libexec", "/usr/include",
              "/usr/share", "/usr/share/dsg", "/usr/share/dsg/configs", libdir,
              f"{libdir}/cmake", f"{libdir}/pkgconfig", qtarchdata,
              f"{qtarchdata}/mkspecs", f"{qtarchdata}/mkspecs/modules", f"{qtarchdata}/mkspecs/features",
              f"{libdir}/qt5", f"{libdir}/qt5/plugins"}
    groups = {key: [] for key in ("runtime", "devel", "widget-devel")}
    for file in sorted(root.rglob("*")):
        path = "/" + file.relative_to(root).as_posix()
        is_dir = file.is_dir() and not file.is_symlink()
        if is_dir and path in shared:
            continue
        if any(char in path for char in ('"', '\n', '%')):
            raise ValueError(f"Unsupported RPM filename: {path!r}")
        groups[category(path, libdir, qtarchdata)].append(("%dir " if is_dir else "") + f'"{path}"')
    for key, paths in groups.items():
        if not paths:
            raise ValueError(f"Empty package: {key}")
        Path(f"{key}.files").write_text("\n".join(paths) + "\n")


if __name__ == "__main__":
    main()
