#!/usr/bin/env bash
# gxde-compressor: archive tools (rofd Rust backend + GUI/data modules).
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

# rofd (Rust): the qttypes proc-macro's cpp crate cannot read struct metadata
# from LTO-thin objects, and --remap-path-prefix breaks its path-based macro
# matching against build.rs-generated closures. Strip both (same as AUR).
# CARGO_HOME + --offline mirror AUR; the tarball must vendor its deps.
export CARGO_HOME="$PWD/cargo-home"
( cd rofd && \
    RUSTFLAGS="$(sed -E 's/--remap-path-prefix=[^ ]*//g' <<< "${RUSTFLAGS:-}")" \
    CFLAGS="$(sed -E 's/-flto[^ ]*|-ffat-lto-objects//g' <<< "${CFLAGS:-}")" \
    CXXFLAGS="$(sed -E 's/-flto[^ ]*|-ffat-lto-objects//g' <<< "${CXXFLAGS:-}")" \
    cargo build --release --offline --locked -p rofd-ffi -p rofd --features rofd/qt-reader )
rv=$(sed -n 's/^version = "\(.*\)"/\1/p' rofd/crates/rofd-ffi/Cargo.toml | head -1)
install -Dm644 "rofd/target/release/librofd_ffi.so" "$stage$libdir/librofd_ffi.so.$rv"
ln -sf "librofd_ffi.so.$rv" "$stage$libdir/librofd_ffi.so.${rv%%.*}"
ln -sf "librofd_ffi.so.$rv" "$stage$libdir/librofd_ffi.so"
install -Dm644 rofd/crates/rofd-ffi/include/rofd.h "$stage/usr/include/rofd.h"
install -Dm755 rofd/target/release/rofd "$stage/usr/bin/rofd"
install -Dm644 rofd/debian/rofd.desktop "$stage/usr/share/applications/rofd.desktop"
install -Dm644 rofd/resources/logo.png "$stage/usr/share/icons/hicolor/256x256/apps/rofd.png"

# Data/prebuilt-tree modules: ship their src/ trees verbatim (mirrors AUR).
for m in zipu gxde-shell-compressor gxde-compressor; do
    cp -a "$m/src/." "$stage/"
done

normalize_stage
