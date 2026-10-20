#!/usr/bin/env bash
set -euo pipefail
libdir=$1
jobs=$2
stage="$PWD/stage"
mkdir -p "$stage"
export LD_LIBRARY_PATH="$stage$libdir${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LIBRARY_PATH="$stage$libdir${LIBRARY_PATH:+:$LIBRARY_PATH}"
export PKG_CONFIG_PATH="$stage$libdir/pkgconfig:$stage/usr/share/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
export CMAKE_PREFIX_PATH="$stage/usr${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
export GO111MODULE=off GOFLAGS='-buildmode=pie -trimpath'
# Fedora keeps asoundlib.h under alsa/, while this vendored Go binding
# includes it as <asoundlib.h>. Add the header directory without editing it.
export CGO_CPPFLAGS="${CPPFLAGS:-} -I/usr/include/alsa" CGO_CFLAGS="${CFLAGS:-} -std=gnu17"
export CGO_CXXFLAGS="${CXXFLAGS:-}" CGO_LDFLAGS="${LDFLAGS:-}"

cmake_build() {
    local name=$1; shift
    cmake -S "$name" -B "build-$name" -G Ninja \
        -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR="${libdir#/usr/}" \
        -DCMAKE_INSTALL_LIBEXECDIR=libexec -DCMAKE_BUILD_TYPE=None \
        -DBUILD_TESTING=OFF "$@"
    cmake --build "build-$name" --parallel "$jobs"
    DESTDIR="$stage" cmake --install "build-$name"
}

make -C golang-gxde-dev install DESTDIR="$stage"
cmake_build disomaster-qt6
mkdir -p build-tools
ln -s ../deepin-gettext-tools/src/policy_ts_convert.py build-tools/deepin-policy-ts-convert
export PATH="$PWD/build-tools:$PATH"
make -C gxde-api -j "$jobs" GOPATH="$stage/usr/share/gocode-gxde:$PWD/gxde-api/gopath"

(cd libgnome-keyring && GPGRT_CONFIG=/usr/bin/gpgrt-config ./configure \
    --prefix=/usr --libdir="$libdir" --sysconfdir=/etc --disable-static \
    --enable-introspection --enable-vala --disable-gtk-doc \
    --disable-maintainer-mode && make -j "$jobs")

for file in gxde-desktop-base/files/*-lizhi; do
    cp "$file" "${file%-lizhi}"
done
if [[ "$(uname -m)" == aarch64 ]]; then distro=arm; else distro=x86; fi
make -C gxde-desktop-schemas build DISTRO="$distro"

PATH="$PWD/dframework-dbus-qt6:$PATH" cmake_build dframework-dbus-qt6
mkdir -p build-gxde-network-utils-qt6
(cd build-gxde-network-utils-qt6 && DFRAMEWORK_PATH="$stage/usr" \
    qmake6 ../gxde-network-utils-qt6 PREFIX=/usr "target.path=$libdir" \
    "LIBS+=-L$stage$libdir" \
    'CONFIG+=no_qt_rpath' 'CONFIG+=nostrip' \
    "QMAKE_CXXFLAGS_RELEASE=${CXXFLAGS:-}" "QMAKE_LFLAGS_RELEASE=${LDFLAGS:-}")
make -C build-gxde-network-utils-qt6 -j "$jobs"
make -C build-gxde-network-utils-qt6 INSTALL_ROOT="$stage" install

cmake_build udisks2-qt6
cmake_build gxde-movie-reborn -DUSE_DXCB=OFF -DCMAKE_POSITION_INDEPENDENT_CODE=ON
cmake_build libdbusmenu-qt6 -DUSE_QT6=ON -DWITH_DOC=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake_build treeland-protocols
cmake_build xdg-desktop-portal-gxde
