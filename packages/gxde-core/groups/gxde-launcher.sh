#!/usr/bin/env bash
# gxde-launcher: the GXDE launcher (Qt6/dtk6).
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

_cmake gxde-launcher

normalize_stage
