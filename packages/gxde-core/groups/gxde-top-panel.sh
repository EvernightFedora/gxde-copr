#!/usr/bin/env bash
# gxde-top-panel: top panel and its plugins (Qt6).
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

_cmake gxde-top-panel-plugins
# gxde-top-panel's CMakeLists runs `apt --version` to pick the deb.cmake
# install branch; the other branch still uses the old filenames. Provide an
# apt stub so it takes the deb.cmake branch (matching AUR).
install -d "$PWD/apt-stub"
printf '#!/bin/sh\necho "apt 0 (build stub)"\n' > "$PWD/apt-stub/apt"
chmod +x "$PWD/apt-stub/apt"
# top-panel does find_program(QT_LRELEASE_EXECUTABLE /usr/lib/qt6/bin/lrelease)
# which is NOTFOUND on Fedora; pre-set the cache var to the toolbin shim.
PATH="$PWD/apt-stub:$PATH" _cmake gxde-top-panel \
    -DQT_LRELEASE_EXECUTABLE="$toolbin/lrelease"

# top-panel also installs com.deepin.dde.Dock.service with
# Exec=/usr/bin/dde-dock — a binary that exists in no package (upstream
# leftover from the pre-rename deb layout). gxde-dock ships the working
# version (Exec=/usr/bin/gxde-dock); drop the broken duplicate here.
rm -f "$stage/usr/share/dbus-1/services/com.deepin.dde.Dock.service"

normalize_stage
