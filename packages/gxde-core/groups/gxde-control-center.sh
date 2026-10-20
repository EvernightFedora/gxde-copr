#!/usr/bin/env bash
# gxde-control-center: the GXDE control center (Qt6/dtk6).
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

_cmake gxde-control-center

normalize_stage
