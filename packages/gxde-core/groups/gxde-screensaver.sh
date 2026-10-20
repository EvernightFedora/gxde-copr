#!/usr/bin/env bash
# gxde-screensaver: deepin-screensaver (Qt6) + gxde-time-screensaver (Qt5).
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

_qmake qmake-qt5 gxde-time-screensaver
_cmake deepin-screensaver -DQT_VERSION_MAJOR=6 -DVERSION="$(_ver deepin-screensaver)" \
    -DAPP_VERSION="$(_ver deepin-screensaver)"

normalize_stage
