#!/usr/bin/env bash
# gxde-terminal: the GXDE terminal (Qt6/dtk6, branch dtk6).
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

_cmake gxde-terminal -DINSTALL_USER_MANUAL=OFF -DVERSION="$(_ver gxde-terminal)" \
    -DAPP_VERSION="$(_ver gxde-terminal)"

normalize_stage
