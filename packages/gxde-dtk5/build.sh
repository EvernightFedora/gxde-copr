#!/usr/bin/env bash
set -euo pipefail
libdir=$1
libexecdir=$2
qtarchdata=$3
qtheaders=$4
common_version=$5
jobs=$6
stage="$PWD/stage"
export LD_LIBRARY_PATH="$stage$libdir${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PKG_CONFIG_PATH="$stage$libdir/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
export CMAKE_PREFIX_PATH="$stage/usr${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"

# The generator must read the schema from this build, not the host's Deepin DTK.
sed -i "s|/usr/share/dsg/configs/|$stage/usr/share/dsg/configs/|g" dtk5gui/src/kernel/kernel.cmake
common=(
    -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_INSTALL_PREFIX=/usr
    # Upstream .pc/.pri templates prepend /usr themselves: use relative GNU dirs.
    "-DCMAKE_INSTALL_LIBDIR=${libdir#/usr/}" "-DCMAKE_INSTALL_LIBEXECDIR=${libexecdir#/usr/}"
    "-DCMAKE_PREFIX_PATH=$stage/usr" "-DMKSPECS_INSTALL_DIR=${qtarchdata#/usr/}/mkspecs/modules"
    "-DFEATURES_INSTALL_DIR=${qtarchdata#/usr/}/mkspecs/features"
    -DCMAKE_SKIP_RPATH=ON -DDTK5=ON -DBUILD_TESTING=OFF -DBUILD_EXAMPLES=OFF -DBUILD_DOCS=OFF
)

# Stage the same Treeland protocol release as gxde-infra, without shipping it in this RPM.
for module in treeland-protocols dtk5common dtklog dtk5core dtk5gui dtk5widget dde-qt5platform-plugins dde-qt5integration; do
    extra=()
    case "$module" in
        dtk5common) extra=("-DDTK_VERSION=$common_version") ;;
        dtklog) extra=(-DBUILD_WITH_SYSTEMD=ON) ;;
        dtk5core) extra=(-DBUILD_WITH_SYSTEMD=ON -DD_DSG_APP_DATA_FALLBACK=/var/dsg/appdata) ;;
        # Fedora's current libqtxdg is Qt6. Use the upstream fallback for Qt5.
        dtk5gui) extra=(-DDTK_DISABLE_LIBXDG=ON -DDTK_DISABLE_EX_IMAGE_FORMAT=ON) ;;
        dtk5widget) extra=(-DBUILD_PLUGINS=OFF -DDTK_STATIC_TRANSLATION=YES) ;;
        dde-qt5platform-plugins)
            # Fedora installs versioned Qt private headers. Never guess a Qt ABI.
            mapfile -t xcb_headers < <(find "$qtheaders" -name qxcbwindow.h -print)
            if (( ${#xcb_headers[@]} != 1 )); then
                echo "Expected one Fedora Qt5 qxcbwindow.h; found ${#xcb_headers[@]}" >&2
                exit 1
            fi
            extra=("-DQT_XCB_PRIVATE_HEADERS=$(dirname "${xcb_headers[0]}")") ;;
        dde-qt5integration) extra=("-DPLUGIN_INSTALL_BASE_DIR=$libdir/qt5/plugins") ;;
    esac
    # Older widget/platform releases use a cache variable instead of VERSION.
    if [[ ! -f "$module/VERSION" && "$module" != dtk5common && "$module" != treeland-protocols ]]; then
        version=$(python3 -c 'import json,re,sys; print(re.match(r"v?(\d+(?:\.\d+)*)", json.load(open("upstream-lock.json"))["components"][sys.argv[1]]["tag"])[1])' "$module")
        extra+=("-DDTK_VERSION=$version")
    fi
    cmake -S "$module" -B "build-$module" "${common[@]}" "${extra[@]}"
    if [[ "$module" == dtk5gui ]]; then
        grep -Fxq 'DEEPIN_WAYLAND_TEST_COMPILE_RESULT:INTERNAL=TRUE' "build-$module/CMakeCache.txt" || {
            echo 'dtk5gui Treeland compile test failed; refusing a build without window dragging' >&2
            exit 1
        }
        grep -Fxq "TreelandProtocols_DIR:PATH=$stage/usr/share/cmake/TreelandProtocols" "build-$module/CMakeCache.txt" || {
            echo 'dtk5gui did not select the staged Treeland protocols' >&2
            exit 1
        }
    fi
    cmake --build "build-$module" --parallel "$jobs"
    DESTDIR="$stage" cmake --install "build-$module"
done
