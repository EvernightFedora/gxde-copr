#!/usr/bin/env bash
# gxde-artwork: themes, icons, wallpapers, sounds, account faces, defaults.
set -euo pipefail
libdir=$1 jobs=$2 common=$3
. "$common"

make -C gxde-icon-theme
# gxde-wallpapers' blur target hardcodes /usr/lib/deepin-api/image-blur
# (deepin-api is not packaged on Fedora). Provide an ImageMagick stub in
# toolbin and rewrite the hardcoded path to use it via PATH.
cat > "$toolbin/image-blur" <<'EOF'
#!/bin/sh
# deepin-api image-blur replacement: image-blur --sigma N INPUT OUTPUT
sigma=30
[ "$1" = "--sigma" ] && { sigma=$2; shift 2; }
magick "$1" -blur "0x${sigma}" "$2"
EOF
chmod 755 "$toolbin/image-blur"
sed -i 's#/usr/lib/deepin-api/image-blur#image-blur#' gxde-wallpapers/Makefile
make -C gxde-wallpapers

make -C gxde-account-faces install DESTDIR="$stage"
chmod 775 "$stage/var/lib/AccountsService" "$stage/var/lib/AccountsService/icons"
install -d "$stage/usr/share/icons"
cp -a gxde-icon-theme/{gxde,deepin,gxde-dark,gxde-Sea} "$stage/usr/share/icons/"
make -C deepin-gtk-theme install DESTDIR="$stage"
cp -a gxde-artwork/etc "$stage/"
install -d "$stage/usr/share/wallpapers/deepin" "$stage/var/cache"
cp -a gxde-wallpapers/deepin "$stage/usr/share/wallpapers/"
cp -a gxde-wallpapers/deepin-community/. gxde-wallpapers/deepin-solidwallpapers/. \
    "$stage/usr/share/wallpapers/deepin/"
cp -a gxde-wallpapers/image-blur "$stage/var/cache/"
make -C gxde-default-settings install DESTDIR="$stage"
# gxde-default-settings-tuning extras (debian/install in AUR)
install -Dm644 gxde-default-settings/tuning/cups-filters/*.pdf \
    -t "$stage/usr/share/deepin-default-settings/cups-filters/"
install -Dm644 gxde-default-settings/tuning/google-chrome/*.tar \
    -t "$stage/usr/share/deepin-default-settings/google-chrome/"
install -Dm644 gxde-default-settings/tuning/fcitx/*.png \
    -t "$stage/usr/share/deepin-default-settings/fcitx/"
make -C gxde-sound-theme install DESTDIR="$stage"

# /usr/share/applications/mimeapps.list is owned by shared-mime-info on
# Fedora (distribution-managed defaults); drop our copy to avoid the file
# conflict, mirroring the /etc config-filtering policy.
rm -f "$stage/usr/share/applications/mimeapps.list"

normalize_stage
