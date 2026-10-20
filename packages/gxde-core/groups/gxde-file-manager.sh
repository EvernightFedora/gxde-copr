#!/usr/bin/env bash
# gxde-file-manager: file manager (+integration) and util-dfm libraries.
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

# KF6 headers (KCodecs) require C++20; -r propagates args to subprojects.
# gxde-dock headers/pc come from the installed gxde-dock-devel package.
_qmake "qmake6 -r" gxde-file-manager VERSION="$(_ver gxde-file-manager)" DISABLE_JEMALLOC=1 \
    "DEFINES+=VERSION=$(_ver gxde-file-manager)" CONFIG+=c++20
_qmake qmake6 gxde-file-manager-integration "DAPP_VERSION=$(_ver gxde-file-manager-integration)"

# F45's OpenSSL headers no longer declare EVP_sm3 (SM3 left the default API).
# dsm3hash.cpp handles a null EVP_MD gracefully (returns {}), so probe-compile
# an EVP_sm3 call and, only where it does not compile, inject a static
# null-returning fallback right after the evp.h include. No-op on F44/VM.
if ! printf '#include <openssl/evp.h>\nint main(void){ return EVP_sm3() ? 0 : 1; }\n' \
        | gcc -x c - -o /tmp/.sm3-probe -lcrypto 2>/dev/null; then
    sed -i '/#include <openssl\/evp.h>/a static const EVP_MD *EVP_sm3() { return nullptr; }' \
        util-dfm/src/dfm-burn/dfm-burn-lib/private/dsm3hash.cpp
fi
rm -f /tmp/.sm3-probe

_cmake util-dfm -DVERSION="$(_ver util-dfm)"

# util-dfm's dfm6-search.pc lists CMake target names (Boostsystem, Threads) in
# Requires: — rpm's pkgconfig dep generator turns them into unsatisfiable
# pkgconfig(...) requires on the devel package (rpm6 ignores
# %global __requires_exclude), and they break pkg-config consumers as well.
# Strip the bogus tokens from the staged .pc files.
find "$stage" -name '*.pc' 2>/dev/null | while read -r pc; do
    sed -i -E '/^Requires/ { s/\bBoostsystem\b//g; s/\bThreads\b//g; s/[[:space:]]{2,}/ /g; s/,[[:space:]]*,/,/g; s/[[:space:]]+$// }' "$pc"
done

normalize_stage
