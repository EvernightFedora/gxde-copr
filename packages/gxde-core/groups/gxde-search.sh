#!/usr/bin/env bash
# gxde-search: grand search (+ its pdfium-based document preview backend).
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

_cmake deepin-pdfium -DVERSION="$(_ver deepin-pdfium)"
# deepin-qdbus-serviceConfig.cmake hardcodes /usr/include/deepin-qdbus-service
# (headers ship in gxde-app-management-devel).
_cmake dde-grand-search -DVERSION="$(_ver dde-grand-search)" \
    -DCMAKE_CXX_FLAGS="${CXXFLAGS:-} -I/usr/include/deepin-qdbus-service"

normalize_stage
