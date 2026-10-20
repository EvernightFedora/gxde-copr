#!/usr/bin/env bash
# gxde-dock: the GXDE dock (Qt6, dtk2-qt6/dtk6).
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

_cmake gxde-dock

normalize_stage
