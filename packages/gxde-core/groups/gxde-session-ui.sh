#!/usr/bin/env bash
# gxde-session-ui: session shell UI (Qt5 main project + Qt6 targets like
# dde-osd and the dde-shutdown ExternalProject).
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

# A global -I/usr/include/qt5 would shadow the Qt6 headers of the Qt6 targets
# and break Qt6 moc output; instead rewrite <QGSettings/QGSettings> to
# <QGSettings>: every subproject pulls the version-correct -I.../QGSettings
# from its gsettings-qt{,6} pkg-config.
grep -rl --include='*.h' --include='*.cpp' '<QGSettings/QGSettings>' gxde-session-ui |
    xargs -r sed -i 's#include <QGSettings/QGSettings>#include <QGSettings>#'
# session-widgets does find_program(QDBUSXML2CPP qdbusxml2cpp); the main
# project is Qt5, so point the toolbin shim at the Qt5 generator.
ln -sf /usr/bin/qdbusxml2cpp-qt5 "$toolbin/qdbusxml2cpp"
_cmake gxde-session-ui

normalize_stage
