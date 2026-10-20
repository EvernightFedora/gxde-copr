#!/usr/bin/env bash
# gxde-app-management: app store components (installer/upgrader/uninstaller),
# deepin-service-manager (ships libqdbusservice, consumed by gxde-search) and
# gxde-requ.
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

# Data/prebuilt-tree modules: ship their src/ trees verbatim (mirrors AUR).
for m in gxde-app-installer gxde-app-upgrader; do
    cp -a "$m/src/." "$stage/"
done
install -d "$stage/usr"
cp -a gxde-app-uninstaller/src/usr/. "$stage/usr/"

_cmake gxde-requ
_cmake deepin-service-manager -DVERSION="$(_ver deepin-service-manager)"

normalize_stage
