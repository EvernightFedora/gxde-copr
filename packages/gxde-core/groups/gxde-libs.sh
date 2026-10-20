#!/usr/bin/env bash
# gxde-libs: internal shared libraries (network-utils-qt6, bernese).
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

# network-utils .pro hardcodes target.path = $$PREFIX/lib and expands the pc
# libdir at parse time; -after moves both to Fedora's libdir.
_qmake qmake6 gxde-network-utils-qt6 \
    -after "target.path=$libdir" "QMAKE_PKGCONFIG_LIBDIR=$libdir"
# GxdeBerneseQt6 cmake config consumed by top-panel / control-center /
# file-manager.
_cmake gxde-bernese
# bernese installs doxygen-generated API man pages; Fedora guidelines say not
# to ship auto-generated man pages.
rm -rf "$stage/usr/share/man"

normalize_stage
