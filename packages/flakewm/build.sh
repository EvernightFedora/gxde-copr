#!/usr/bin/env bash
# Build flakewm (GXDE Wayland compositor) via cmake.
# Run from spec %build with two args: %{_libdir} and %{_smp_build_ncpus}.
set -euo pipefail
libdir=$1
jobs=$2
stage="$PWD/stage"
mkdir -p "$stage"

cmake -S flakewm -B build -G Ninja \
    -DCMAKE_BUILD_TYPE=None \
    -DCMAKE_INSTALL_PREFIX=/usr \
    -DCMAKE_INSTALL_BINDIR=bin \
    -DCMAKE_INSTALL_LIBDIR="${libdir#/usr/}" \
    -DWLCOM_EXAMPLES=OFF \
    -DWLCOM_UKUI_THEME=ON \
    -DWLCOM_WLROOTS_RENDERERS=gles2,vulkan
cmake --build build --parallel "$jobs"
DESTDIR="$stage" cmake --install build
