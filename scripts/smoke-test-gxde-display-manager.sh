#!/usr/bin/env bash
set -euo pipefail

# gxdm binaries
for executable in gxdm gxdm-emergency-mode gxdmr; do
    command -v "$executable" >/dev/null
done

# gxdm helper in libexec
test -x /usr/lib/gxdm/gxdm-helper || test -x /usr/libexec/gxdm/gxdm-helper

# PAM files (Fedora-specific, not upstream Arch-style)
for pam in gxdm gxdm-autologin gxdm-greeter gxdm-rescue; do
    test -f "/etc/pam.d/$pam"
done

# Config
test -f /etc/gxdm/OMG.conf

# systemd services
test -f /usr/lib/systemd/system/gxdm.service
test -f /usr/lib/systemd/system/gxdm-rescue.service

# Greeter session
test -d /usr/share/gxdm/themes || test -d /usr/share/gxdm/translations-qt6

# DBus
test -d /usr/share/dbus-1/system.d

# Lock file
python3 - <<'PY'
import json
from pathlib import Path
lock = json.loads(Path('/usr/share/doc/gxde-display-manager/upstream-lock.json').read_text())
assert len(lock['components']) == 3  # 2 modules + MavenPro-OFL
assert lock['components']['gxde-display-manager']['tag'] == '1.3.2-gxde2'
assert lock['components']['gxdm-emergency-mode']['tag'] == '1.0.0-gxde2'
assert lock['components']['MavenPro-OFL']['commit'] == '1c21ee500b7b87a4871696519fc84107a1a001df'
PY
