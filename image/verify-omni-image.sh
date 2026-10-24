#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ] || [ ! -s "$1" ]; then
  echo "Usage: image/verify-omni-image.sh PATH_TO_BUILT_ISO" >&2
  exit 2
fi
for tool in xorriso unsquashfs python3; do
  command -v "$tool" >/dev/null || { echo "Required verification tool missing: $tool" >&2; exit 1; }
done

ISO="$(realpath "$1")"
TEMP="$(mktemp -d)"
trap 'pkill -9 -x xfconfd 2>/dev/null || true; pkill -9 -x tumblerd 2>/dev/null || true; rm -rf "$TEMP" 2>/dev/null || rm -rf "$TEMP" 2>/dev/null || true' EXIT
xorriso -osirrox on -indev "$ISO" -extract /live/filesystem.squashfs "$TEMP/filesystem.squashfs"
# Extract only the regular files and one symlink verified below. This avoids
# creating /dev character/block nodes or restoring privileged ownership/xattrs.
VERIFY_PATHS=(
  usr/bin/nexus-omniloader
  usr/bin/wasmtime
  usr/lib/nexus/nexus-waydroid-preflight
  usr/lib/nexus/nexus-wine-office-profile
  usr/lib/nexus/nexus-omniloader-ui.py
  usr/lib/nexus/nexus-system-sound.py
  etc/xdg/autostart/nexus-system-sound.desktop
  usr/share/applications/nexus-wine-office-profile.desktop
  etc/modules-load.d/nexus-waydroid.conf
  etc/systemd/system/nexus-omnios-binfmt.service
  etc/systemd/system/multi-user.target.wants/nexus-omnios-binfmt.service
  var/lib/dpkg/arch
  var/lib/dpkg/status
)
unsquashfs -no-xattrs -no-progress -f -d "$TEMP/rootfs" \
  "$TEMP/filesystem.squashfs" "${VERIFY_PATHS[@]}" >/dev/null
ROOTFS="${ROOTFS:-$TEMP/rootfs}"

ROOTFS="$TEMP/rootfs" python3 - <<'PY'
import os
from pathlib import Path

root = Path(os.environ["ROOTFS"])
for binary in ("usr/bin/nexus-omniloader", "usr/bin/wasmtime"):
    item = root / binary
    assert item.is_file() and os.access(item, os.X_OK), f"missing executable in ISO: /{binary}"
waydroid_preflight = root / "usr/lib/nexus/nexus-waydroid-preflight"
assert waydroid_preflight.is_file() and os.access(waydroid_preflight, os.X_OK), "Waydroid Binder preflight missing"
office_profile = root / "usr/lib/nexus/nexus-wine-office-profile"
assert office_profile.is_file() and os.access(office_profile, os.X_OK), "isolated Wine Office profile helper missing"
assert (root / "usr/lib/nexus/nexus-omniloader-ui.py").is_file(), "Nexus Cyber-Glass dialog helper missing"
assert (root / "usr/lib/nexus/nexus-system-sound.py").is_file(), "Nexus synthesized sound helper missing"
assert (root / "etc/xdg/autostart/nexus-system-sound.desktop").is_file(), "Nexus startup sound hook missing"
assert (root / "usr/share/applications/nexus-wine-office-profile.desktop").is_file(), "Office profile desktop launcher missing"
assert (root / "etc/modules-load.d/nexus-waydroid.conf").read_text().strip() == "binder_linux"

unit = root / "etc/systemd/system/nexus-omnios-binfmt.service"
enabled = root / "etc/systemd/system/multi-user.target.wants/nexus-omnios-binfmt.service"
assert unit.is_file(), "systemd binfmt unit missing from ISO"
assert enabled.is_symlink(), "systemd binfmt unit is not enabled in ISO"
assert "--register-binfmt" in unit.read_text()

arch_file = root / "var/lib/dpkg/arch"
assert arch_file.is_file() and "i386" in arch_file.read_text().splitlines(), "Wine i386 architecture missing"

status_file = root / "var/lib/dpkg/status"
paragraphs = status_file.read_text(errors="replace").split("\n\n")
installed = set()
for paragraph in paragraphs:
    fields = {}
    for line in paragraph.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            fields[key] = value
    if fields.get("Status") == "install ok installed":
        installed.add((fields.get("Package"), fields.get("Architecture", "all")))

for package in ("chromium", "aapt", "waydroid", "weston", "wine64", "winbind", "cabextract", "winetricks", "fonts-liberation", "alsa-utils"):
    assert any(name == package for name, _ in installed), f"required installed package missing from ISO: {package}"
assert ("wine32", "i386") in installed, "wine32:i386 missing from ISO"

print("Nexus OmniSubsystem files, packages, i386 architecture, and enabled systemd unit are present in the ISO.")
PY

"$ROOTFS/usr/bin/wasmtime" --version
