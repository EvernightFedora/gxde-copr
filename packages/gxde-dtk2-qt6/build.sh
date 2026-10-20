#!/usr/bin/env bash
set -euo pipefail
libdir=$1
jobs=$2
stage="$PWD/stage"
mkdir -p "$stage" "$PWD/pc" build-dtk2widget-qt6 build-gxde-qt6-integration
export LD_LIBRARY_PATH="$stage$libdir${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PKG_CONFIG_PATH="$PWD/pc${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
qmake_args=("PREFIX=/usr" "LIB_INSTALL_DIR=$libdir" 'CONFIG+=no_qt_rpath' 'CONFIG+=nostrip'
            "QMAKE_CFLAGS_RELEASE=${CFLAGS:-}" "QMAKE_CXXFLAGS_RELEASE=${CXXFLAGS:-}"
            "QMAKE_LFLAGS_RELEASE=${LDFLAGS:-}")

(cd build-dtk2widget-qt6 && qmake6 -r ../dtk2widget-qt6 "${qmake_args[@]}")
make -C build-dtk2widget-qt6 -j "$jobs"
make -C build-dtk2widget-qt6 INSTALL_ROOT="$stage" install
python3 - "$stage$libdir/pkgconfig/dtk2widget.pc" "$PWD/pc/dtk2widget.pc" "$stage" <<'PY'
from pathlib import Path
import sys
src, dst, stage = sys.argv[1:]
content = Path(src).read_text()
content = content.replace('prefix=/usr', f'prefix={stage}/usr')
content = content.replace('libdir=/usr', f'libdir={stage}/usr')
content = content.replace('Requires: dtkcore', 'Requires: dtk6core')
if 'Libs: -L${libdir}' not in content:
    content = content.replace('Libs: -ldtk2widget', 'Libs: -L${libdir} -ldtk2widget')
Path(dst).write_text(content)
PY

(cd build-gxde-qt6-integration && qmake6 -r ../gxde-qt6-integration "${qmake_args[@]}")
make -C build-gxde-qt6-integration -j "$jobs"
