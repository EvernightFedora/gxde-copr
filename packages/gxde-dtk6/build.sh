#!/usr/bin/env bash
set -euo pipefail
libdir=$1
libexecdir=$2
qtarchdata=$3
qtheaders=$4
jobs=$5
stage="$PWD/stage"
export LD_LIBRARY_PATH="$stage$libdir${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PKG_CONFIG_PATH="$stage$libdir/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
export CMAKE_PREFIX_PATH="$stage/usr${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
common=(
    -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX=/usr
    "-DCMAKE_INSTALL_LIBDIR=${libdir#/usr/}" "-DCMAKE_INSTALL_LIBEXECDIR=${libexecdir#/usr/}"
    "-DCMAKE_PREFIX_PATH=$stage/usr" "-DMKSPECS_INSTALL_DIR=${qtarchdata#/usr/}/mkspecs/modules"
    "-DFEATURES_INSTALL_DIR=${qtarchdata#/usr/}/mkspecs/features"
    -DCMAKE_SKIP_RPATH=ON -DBUILD_TESTING=OFF -DBUILD_EXAMPLES=OFF -DBUILD_DOCS=OFF
)
# treeland-protocols is staged only for dtk6gui and never installed by the spec. Fedora's
# 0.5.x personalization protocol uses different request opcodes from flakewm's, and
# without Treeland dtk6gui has no Wayland window move (DTitlebar cannot drag windows).
for module in treeland-protocols dtk6log dtk6core dtk6gui dtk6widget dtk6declarative dde-qt6platform-plugins qt6integration; do
    extra=()
    case "$module" in
        dtk6log) extra=(-DBUILD_WITH_QT6=ON -DBUILD_WITH_SYSTEMD=ON) ;;
        dtk6core) extra=(-DBUILD_WITH_SYSTEMD=ON -DD_DSG_APP_DATA_FALLBACK=/var/dsg/appdata) ;;
        dtk6gui) extra=(-DDTK_DISABLE_EX_IMAGE_FORMAT=ON) ;;
        dtk6widget) extra=(-DBUILD_PLUGINS=OFF) ;;
        dtk6declarative) extra=("-DQML_INSTALL_DIR=${libdir#/usr/}/qt6/qml") ;;
        dde-qt6platform-plugins)
            mapfile -t xcb_headers < <(find "$qtheaders" -name qxcbwindow.h -print)
            if (( ${#xcb_headers[@]} != 1 )); then
                echo "Expected one Fedora Qt6 qxcbwindow.h; found ${#xcb_headers[@]}" >&2
                exit 1
            fi
            extra=("-DQT_XCB_PRIVATE_HEADERS=$(dirname "${xcb_headers[0]}")") ;;
        qt6integration)
            version=$(python3 -c 'import json,re; print(re.match(r"v?(\d+(?:\.\d+)*)", json.load(open("upstream-lock.json"))["components"]["qt6integration"]["tag"])[1])')
            extra=("-DDTK_VERSION=$version" "-DPLUGIN_INSTALL_BASE_DIR=${libdir#/usr/}/qt6/plugins") ;;
    esac
    cmake -S "$module" -B "build-$module" "${common[@]}" "${extra[@]}"
    if [[ "$module" == dtk6gui ]]; then
        grep -Fxq 'DEEPIN_WAYLAND_TEST_COMPILE_RESULT:INTERNAL=TRUE' "build-$module/CMakeCache.txt" || {
            echo 'dtk6gui Treeland compile test failed; refusing a build without window dragging' >&2
            exit 1
        }
        grep -Fxq "TreelandProtocols_DIR:PATH=$stage/usr/share/cmake/TreelandProtocols" "build-$module/CMakeCache.txt" || {
            echo 'dtk6gui did not select the staged Treeland protocols' >&2
            exit 1
        }
    fi
    cmake --build "build-$module" --parallel "$jobs"
    DESTDIR="$stage" cmake --install "build-$module"
done
