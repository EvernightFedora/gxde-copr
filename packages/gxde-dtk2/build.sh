#!/usr/bin/env bash
set -euo pipefail
libdir=$1
qtarchdata=$2
version=$3
jobs=$4
stage="$PWD/stage"
version=${version%%.gxde*}
mkdir -p "$stage" "$PWD/pc" build-dde-qt-dbus-factory build-dtk2widget build-gxde-qt5integration
export LD_LIBRARY_PATH="$stage$libdir${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PKG_CONFIG_PATH="$PWD/pc${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
qmake_args=("PREFIX=/usr" "LIB_INSTALL_DIR=$libdir" "INCLUDEPATH+=/usr/include/qt5"
            'CONFIG+=no_qt_rpath' 'CONFIG+=nostrip' "QMAKE_CFLAGS_RELEASE=${CFLAGS:-}" "QMAKE_CXXFLAGS_RELEASE=${CXXFLAGS:-}"
            "QMAKE_LFLAGS_RELEASE=${LDFLAGS:-}")
mkdir -p "$PWD/build-tools"
ln -s "$(command -v lrelease-qt5)" "$PWD/build-tools/lrelease"
export PATH="$PWD/build-tools:$PATH"
qmake-qt5 -v
(cd build-dde-qt-dbus-factory && qmake-qt5 ../dde-qt-dbus-factory "${qmake_args[@]}")
make -C build-dde-qt-dbus-factory -j "$jobs"
make -C build-dde-qt-dbus-factory INSTALL_ROOT="$stage" install
python3 - "$stage$libdir/pkgconfig/dframeworkdbus.pc" "$PWD/pc/dframeworkdbus.pc" "$stage" <<'PY'
from pathlib import Path
import sys
src, dst, stage = sys.argv[1:]
s = Path(src).read_text()
s = s.replace('prefix=/usr', f'prefix={stage}/usr')
s = s.replace('libdir=/usr', f'libdir={stage}/usr')
s = s.replace('Libs: ', 'Libs: -L${libdir} ', 1)
Path(dst).write_text(s)
PY
(cd build-dtk2widget && qmake-qt5 -r ../dtk2widget "${qmake_args[@]}" "VERSION=$version")
make -C build-dtk2widget -j "$jobs"
make -C build-dtk2widget INSTALL_ROOT="$stage" install
python3 - "$stage$libdir/pkgconfig/dtkwidget.pc" "$PWD/pc/dtkwidget.pc" "$stage" <<'PY'
from pathlib import Path
import sys
src, dst, stage = sys.argv[1:]
s = Path(src).read_text().replace('prefix=/usr', f'prefix={stage}/usr').replace('libdir=/usr', f'libdir={stage}/usr')
s = s.replace('Libs: ', 'Libs: -L${libdir} ', 1)
Path(dst).write_text(s)
PY
(cd build-gxde-qt5integration && qmake-qt5 -r ../gxde-qt5integration "${qmake_args[@]}")
make -C build-gxde-qt5integration -j "$jobs"
