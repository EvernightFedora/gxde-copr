#!/usr/bin/env bash
# Build one pinned GXDE optional AUR application in the RPM working tree.
set -euo pipefail
name=$1 tag=$2 libdir=$3 jobs=$4
stage="$PWD/stage"
mkdir -p "$stage" "$PWD/toolbin"

# Fedora installs Qt linguist binaries with explicit version suffixes.
ln -sf /usr/bin/lrelease-qt6 "$PWD/toolbin/lrelease"
ln -sf /usr/bin/lupdate-qt6 "$PWD/toolbin/lupdate"
ln -sf /usr/bin/lconvert-qt6 "$PWD/toolbin/lconvert"
install -m 0755 deepin-policy-ts-convert "$PWD/toolbin/deepin-policy-ts-convert"
install -m 0755 deepin-desktop-ts-convert "$PWD/toolbin/deepin-desktop-ts-convert"
export PATH="$PWD/toolbin:$PATH"

# Upstream translation scripts use Arch/Debian absolute paths. Rewrite only
# the extracted build tree to point at the RPM-local toolbin counterparts.
while IFS= read -r -d '' script; do
    sed -i \
        -e "s#/usr/lib/qt6/bin/#$PWD/toolbin/#g" \
        -e "s#/usr/lib/x86_64-linux-gnu/qt6/bin/#$PWD/toolbin/#g" \
        -e "s#/usr/bin/deepin-desktop-ts-convert#$PWD/toolbin/deepin-desktop-ts-convert#g" \
        "$script"
done < <(find upstream -type f -name '*.sh' -print0)

case "$name" in
    gxde-downloader-neo)
        cp -a upstream/src/. "$stage/"
        ;;
    gxde-hardware-viewer)
        make -C upstream build -j "$jobs"
        make -C upstream install DESTDIR="$stage"
        ;;
    gxde-boot-maker|gxde-filetransfer|gxde-image-viewer|gxde-music|gxde-screen-recorder|gxde-voice-recorder)
        if [[ $name == gxde-music ]]; then
            (cd upstream/src/music-player && ./update-translation.sh)
        fi
        qmake_opts=(PREFIX=/usr CONFIG+=no_qt_rpath CONFIG+=nostrip
                    "QMAKE_CFLAGS_RELEASE=$CFLAGS" "QMAKE_CXXFLAGS_RELEASE=$CXXFLAGS"
                    "QMAKE_LFLAGS_RELEASE=$LDFLAGS" "LIB_INSTALL_DIR=$libdir"
                    "DEFINES+=VERSION=$tag")
        if [[ $name == gxde-music ]]; then qmake_opts+=(BUNDLED_MPRIS=1); fi
        if [[ $name == gxde-screen-recorder ]]; then
            qmake_opts+=("VERSION=$tag" "VERSION_UPSTREAM=$tag")
        fi
        (cd upstream && qmake6 "${qmake_opts[@]}" && make -j "$jobs" &&
         make INSTALL_ROOT="$stage" install)
        if [[ $name == gxde-music ]]; then
            rm -rf "$stage/usr/include" "$stage/usr/lib/pkgconfig" \
                "$stage/usr/lib64/pkgconfig" "$stage/usr/lib/qt6" "$stage/usr/lib64/qt6"
        fi
        ;;
    *)
        cmake_opts=(-DCMAKE_BUILD_TYPE=None -DCMAKE_INSTALL_PREFIX=/usr
                    "-DCMAKE_INSTALL_LIBDIR=${libdir#/usr/}"
                    -DBUILD_TESTING=OFF "-DVERSION=$tag" "-DAPP_VERSION=$tag"
                    "-DQt6_LRELEASE_EXECUTABLE=$PWD/toolbin/lrelease")
        case "$name" in
            gxde-clone) cmake_opts+=(-DDISABLE_DFM_PLUGIN=YES) ;;
            gxde-log-viewer|gxde-reader|gxde-roller)
                cmake_opts+=(-DCMAKE_SAFETYTEST_ARG=CMAKE_SAFETYTEST_ARG_OFF) ;;
        esac
        if [[ $name == gxde-roller ]]; then
            cmake_opts+=("-DCOMPRESSOR_PLUGIN_PATH=$libdir/deepin-compressor/plugins")
        fi
        cmake -S upstream -B build -G Ninja "${cmake_opts[@]}"
        cmake --build build --parallel "$jobs"
        DESTDIR="$stage" cmake --install build
        ;;
esac

# Arch/Debian installs may hardcode /usr/lib or a multiarch subdirectory.
mkdir -p "$stage$libdir"
for triplet in x86_64-linux-gnu aarch64-linux-gnu; do
    if [[ -d $stage/usr/lib/$triplet ]]; then
        cp -a "$stage/usr/lib/$triplet/." "$stage$libdir/"
        rm -rf "$stage/usr/lib/$triplet"
    fi
done
if [[ $libdir != /usr/lib && -d $stage/usr/lib ]]; then
    for path in "$stage/usr/lib/"*.so "$stage/usr/lib/"*.so.* \
                "$stage/usr/lib/qt6" "$stage/usr/lib/pkgconfig"; do
        [[ -e $path || -L $path ]] || continue
        mv "$path" "$stage$libdir/"
    done
fi
if [[ -d $stage/usr/sbin ]]; then
    mkdir -p "$stage/usr/bin"
    cp -a "$stage/usr/sbin/." "$stage/usr/bin/"
    rm -rf "$stage/usr/sbin"
fi
