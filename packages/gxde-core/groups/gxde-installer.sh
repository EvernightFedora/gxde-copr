#!/usr/bin/env bash
# gxde-installer: deepin-installer-reborn timezone message catalogs. The
# bundle (mirroring AUR gxde-core-git) ships only the timezone translations
# from this module, not the installer itself.
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

local_po=build-timezones
for po in deepin-installer-reborn/src/third_party/timezones/*/deepin-installer-timezones.po; do
    d="$local_po/$(basename "$(dirname "$po")")/LC_MESSAGES"
    mkdir -p "$d"
    msgfmt -o "$d/deepin-installer-timezones.mo" "$po"
done
install -d "$stage/usr/share/locale"
cp -a build-timezones/. "$stage/usr/share/locale/"

normalize_stage
