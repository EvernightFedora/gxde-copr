# Shared build preamble for gxde-core split packages. Sourced by each group's
# build.sh, which is invoked from the spec %build as:
#   bash %{SOURCE100} "%{_libdir}" "%{_smp_build_ncpus}" "%{SOURCE101}"
# Expects the sourcing script to have set: libdir, jobs (and set -euo pipefail).
# Produces $PWD/stage as the final file tree; the spec %install copies it to
# the buildroot. Adaptation history: packages/gxde-core/PATCHES.md.

stage="$PWD/stage"
mkdir -p "$stage"

export LD_LIBRARY_PATH="$stage$libdir${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LIBRARY_PATH="$stage$libdir${LIBRARY_PATH:+:$LIBRARY_PATH}"
export PKG_CONFIG_PATH="$stage$libdir/pkgconfig:$stage/usr/share/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
export CMAKE_PREFIX_PATH="$stage/usr${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
export XDG_DATA_DIRS="$stage/usr/share${XDG_DATA_DIRS:+:$XDG_DATA_DIRS}"

# Fedora suffixes the Qt linguist tools (lrelease-qt5/-qt6) but upstream
# translate_generation.sh scripts call unsuffixed `lrelease`. Provide shims;
# _qmake/_cmake flip lrelease to the Qt version matching the module.
toolbin="$PWD/toolbin"
mkdir -p "$toolbin"
ln -sf /usr/bin/lrelease-qt6 "$toolbin/lrelease"
ln -sf /usr/bin/lupdate-qt6 "$toolbin/lupdate"
ln -sf /usr/bin/lconvert-qt6 "$toolbin/lconvert"
# Fedora suffixes qdbusxml2cpp too (-qt5/-qt6); modules do
# find_program(QDBUSXML2CPP qdbusxml2cpp) which searches PATH. Default to the
# Qt6 tool; Qt5 projects flip the symlink before their cmake run.
ln -sf /usr/bin/qdbusxml2cpp-qt6 "$toolbin/qdbusxml2cpp"
# deepin-gettext-tools is not packaged on Fedora; %prep copies the vendored
# scripts into cwd for groups that need them (guarded installs).
if [[ -f deepin-policy-ts-convert ]]; then
    install -m 0755 deepin-policy-ts-convert "$toolbin/deepin-policy-ts-convert"
fi
if [[ -f deepin-desktop-ts-convert ]]; then
    install -m 0755 deepin-desktop-ts-convert "$toolbin/deepin-desktop-ts-convert"
    # `|| true`: grep exits 1 on no match, which pipefail+set -e would fatal.
    { grep -rl --include='*.sh' '/usr/bin/deepin-desktop-ts-convert' . 2>/dev/null || true; } | while read -r f; do
        sed -i "s#/usr/bin/deepin-desktop-ts-convert#$toolbin/deepin-desktop-ts-convert#g" "$f"
    done
fi
export PATH="$toolbin:$PATH"

# Upstream translate scripts hardcode Debian/Arch Qt tool paths
# (/usr/lib/qt6/bin/lrelease, /usr/lib/x86_64-linux-gnu/qt6/bin/...) that do
# not exist on Fedora. Point every hardcoded path at the toolbin shims so the
# scripts' `[ -f ... ]` probes keep working and follow the per-module Qt flip.
{ grep -rl --include='*.sh' \
    -e '/usr/lib/qt6/bin/' -e '/usr/lib/qt5/bin/' \
    -e '/usr/lib/x86_64-linux-gnu/qt6/bin/' -e '/usr/lib/x86_64-linux-gnu/qt5/bin/' \
    . 2>/dev/null || true; } | while read -r f; do
    sed -i \
        -e "s#/usr/lib/qt6/bin/#$toolbin/#g" \
        -e "s#/usr/lib/qt5/bin/#$toolbin/#g" \
        -e "s#/usr/lib/x86_64-linux-gnu/qt6/bin/#$toolbin/#g" \
        -e "s#/usr/lib/x86_64-linux-gnu/qt5/bin/#$toolbin/#g" \
        "$f"
done

# Several modules unconditionally `set(CMAKE_CXX_FLAGS "-g -Wall")`, wiping the
# %set_build_flags hardening specs (PIE, FORTIFY, annobin) and breaking PIE
# links. Make them append.
{ grep -rl --include=CMakeLists.txt --include='*.cmake' \
    -E '^[[:space:]]*set\(CMAKE_CXX_FLAGS "' . 2>/dev/null || true; } | while read -r f; do
    sed -i -E 's#^([[:space:]]*)set\(CMAKE_CXX_FLAGS "([^"$]*)"#\1set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} \2"#' "$f"
done

# Rewrite staging /usr paths in installed .pc files so later components in the
# same group link against the staging tree. Fedora keeps arch pkgconfig in
# libdir.
_stage_pcs() {
    mkdir -p "$PWD/pc"
    local f
    for f in "$stage$libdir/pkgconfig"/*.pc "$stage/usr/share/pkgconfig"/*.pc; do
        [[ -e $f ]] || continue
        sed -E "s#(^[a-z_]+=|-I|-L)/usr(/|\$)#\1$stage/usr\2#g" "$f" > "$PWD/pc/${f##*/}"
    done
    export PKG_CONFIG_PATH="$PWD/pc${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
}

_cmake() {
    local name=$1; shift
    ln -sf /usr/bin/lrelease-qt6 "$toolbin/lrelease"
    cmake -S "$name" -B "build-$name" -G Ninja \
        -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_INSTALL_LIBDIR="${libdir#/usr/}" \
        -DCMAKE_INSTALL_LIBEXECDIR=libexec -DCMAKE_BUILD_TYPE=None \
        -DBUILD_TESTING=OFF \
        -DQt5_LRELEASE_EXECUTABLE=/usr/bin/lrelease-qt5 \
        -DQt6_LRELEASE_EXECUTABLE="$toolbin/lrelease" "$@"
    cmake --build "build-$name" --parallel "$jobs"
    DESTDIR="$stage" cmake --install "build-$name"
    _stage_pcs
}

_qmake() {
    local qm=$1 name=$2; shift 2
    # $qm may carry flags (e.g. "qmake6 -r"); split into an array so the
    # whole string is not treated as a single command name.
    local -a qmcmd
    read -r -a qmcmd <<< "$qm"
    case $qm in
        *qt5*) ln -sf /usr/bin/lrelease-qt5 "$toolbin/lrelease" ;;
        *)     ln -sf /usr/bin/lrelease-qt6 "$toolbin/lrelease" ;;
    esac
    mkdir -p "build-$name"
    ( cd "build-$name" && "${qmcmd[@]}" "../$name" PREFIX=/usr "LIB_INSTALL_DIR=$libdir" \
        CONFIG+=no_qt_rpath CONFIG+=nostrip \
        "INCLUDEPATH+=$stage/usr/include" "LIBS+=-L$stage$libdir" \
        QMAKE_CFLAGS_RELEASE="${CFLAGS:-}" QMAKE_CXXFLAGS_RELEASE="${CXXFLAGS:-}" \
        QMAKE_LFLAGS_RELEASE="${LDFLAGS:-}" "$@" && make -j "$jobs" )
    make -C "build-$name" INSTALL_ROOT="$stage" install
    _stage_pcs
}

_ver() {
    sed -n '1s/.*(\([0-9]*:\)\?\([0-9.]*\).*/\2/p' "$1/debian/changelog"
}

# Debian→Fedora layout normalization + config filtering + exec-bit fixes
# (mirrors AUR package()); run at the end of each group build.
normalize_stage() {
    ( cd "$stage"
      install -d usr/lib
      if [[ -d lib ]]; then
          cp -a lib/. usr/lib/ && rm -r lib
      fi
      if [[ -d usr/sbin ]]; then
          install -d usr/bin && mv usr/sbin/* usr/bin/ && rmdir usr/sbin
      fi
      for d in usr/lib/*-linux-gnu; do
          [[ -d $d ]] || continue
          cp -a "$d/." usr/lib/ && rm -r "$d"
      done
      # Do not install configs that change system behavior; the Fedora
      # equivalents are owned by their own packages.
      rm -rf etc/X11/xinit/xinitrc.d/50-systemd-user.sh etc/X11/Xsession.d \
          etc/X11/xorg.conf.d etc/sudoers.d etc/modprobe.d etc/systemd \
          etc/udisks2 etc/acpi etc/default/grub.d etc/grub.d etc/gimp
      [[ -d etc ]] && find etc -depth -type d -empty -delete
      # Some modules install executables via install(FILES) without exec bit;
      # Debian relies on dh_fixperms. Restore exec bits.
      [[ -d usr/bin ]] && find usr/bin -type f -exec chmod 755 {} +
      if [[ -d usr/libexec ]]; then
          while IFS= read -r -d '' f; do
              [[ $(head -c2 "$f") == '#!' ]] && chmod 755 "$f"
          done < <(find usr/libexec -type f ! -perm -u+x -print0)
      fi
      true )
}
