#!/usr/bin/env bash
# gxde-polkit-agent: polkit authentication agent + gnomekeyring extension.
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

_qmake qmake-qt5 gxde-polkit-agent
_qmake qmake-qt5 dpa-ext-gnomekeyring

normalize_stage
