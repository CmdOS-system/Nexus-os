#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$ROOT/.." && pwd)"
BUILD="$ROOT/build.sh"
PACKAGES="$ROOT/desktop.list.chroot"
IDENTITY="$ROOT/includes/etc/nexus-os-release"
LAUNCHER="$ROOT/includes/usr/local/bin/nexus-agent"
DESKTOP="$ROOT/includes/usr/share/applications/nexus-agent.desktop"
BOOT_UNIT="$ROOT/includes/etc/systemd/system/nexus-boot-ready.service"
BOOT_HOOK="$ROOT/hooks/010-enable-nexus-boot-ready.hook.chroot"
GRUB_HOOK="$ROOT/hooks/020-unattended-grub.hook.binary"
BOOT_MARKER="$ROOT/includes/usr/local/libexec/nexus-boot-ready"
CONTROL_CENTER="$ROOT/includes/opt/nexus/control-center.py"
HORIZON="$ROOT/includes/opt/nexus/horizon.py"
HORIZON_DESKTOP="$ROOT/includes/usr/share/applications/nexus-horizon.desktop"
HORIZON_LAUNCHER="$ROOT/includes/usr/local/bin/nexus-horizon"
HORIZON_PANEL="$ROOT/includes/opt/nexus/horizon-panel.py"
HORIZON_PANEL_DESKTOP="$ROOT/includes/usr/share/applications/nexus-horizon-panel.desktop"
HORIZON_SHORTCUTS="$ROOT/includes/etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-keyboard-shortcuts.xml"
CONTROL_DESKTOP="$ROOT/includes/usr/share/applications/nexus-control-center.desktop"
INSTALLER_PREVIEW="$ROOT/includes/opt/nexus/installer-preview.py"
INSTALLER_DESKTOP="$ROOT/includes/usr/share/applications/nexus-installer-preview.desktop"
OMNI_PACKAGES="$ROOT/package-lists/omnios.list.chroot"
OMNI_ARCHIVE="$ROOT/archives/trixie-backports.list.chroot"
OMNI_HOOK="$ROOT/hooks/050-enable-nexus-omnios-binfmt.hook.chroot"
OMNI_UNIT="$ROOT/includes/etc/systemd/system/nexus-omnios-binfmt.service"
OMNI_DESKTOP="$ROOT/includes/usr/share/applications/nexus-omnisubsystem.desktop"
OMNI_STAGE="$ROOT/stage-omni-subsystem.sh"
OMNI_ISO_VERIFY="$ROOT/verify-omni-image.sh"
OMNI_RUNTIME_SMOKE="$ROOT/runtime-smoke.sh"
WAYDROID_PREFLIGHT="$ROOT/includes/usr/lib/nexus/nexus-waydroid-preflight"
WAYDROID_HOOK="$ROOT/hooks/040-waydroid-binder.hook.chroot"
WINE_OFFICE_PROFILE="$ROOT/includes/usr/lib/nexus/nexus-wine-office-profile"

bash -n "$ROOT/validate.sh"
bash -n "$BUILD"
bash -n "$LAUNCHER"
bash -n "$HORIZON_LAUNCHER"
bash -n "$BOOT_HOOK"
sh -n "$GRUB_HOOK"
sh -n "$ROOT/auto/config"
sh -n "$OMNI_HOOK"
bash -n "$OMNI_STAGE"
bash -n "$OMNI_ISO_VERIFY"
bash -n "$OMNI_RUNTIME_SMOKE"
sh -n "$WAYDROID_PREFLIGHT"
sh -n "$WAYDROID_HOOK"
sh -n "$WINE_OFFICE_PROFILE"
bash -n "$BOOT_MARKER"

for file in "$PACKAGES" "$IDENTITY" "$LAUNCHER" "$DESKTOP" "$BOOT_UNIT" "$BOOT_HOOK" "$GRUB_HOOK" "$BOOT_MARKER" "$CONTROL_CENTER" "$CONTROL_DESKTOP" "$HORIZON" "$HORIZON_DESKTOP" "$HORIZON_LAUNCHER" "$HORIZON_SHORTCUTS" "$HORIZON_PANEL" "$HORIZON_PANEL_DESKTOP" "$INSTALLER_PREVIEW" "$INSTALLER_DESKTOP" "$OMNI_PACKAGES" "$OMNI_ARCHIVE" "$OMNI_HOOK" "$WAYDROID_HOOK" "$WAYDROID_PREFLIGHT" "$WINE_OFFICE_PROFILE" "$OMNI_UNIT" "$OMNI_DESKTOP" "$OMNI_STAGE" "$OMNI_ISO_VERIFY" "$OMNI_RUNTIME_SMOKE" "$ROOT/auto/config"; do
  test -s "$file" || { echo "Missing required image source: $file" >&2; exit 1; }
done

for package in task-xfce-desktop network-manager ca-certificates python3-tk libsecret-tools; do
  grep -qx "$package" "$PACKAGES"
done

grep -q 'NAME="Nexus OS"' "$IDENTITY"
grep -q '^ID=nexus$' "$IDENTITY"
grep -q '^ID_LIKE=debian$' "$IDENTITY"
grep -q '^Name=Nexus Agent$' "$DESKTOP"
grep -q '^Name=Nexus Control Center$' "$CONTROL_DESKTOP"
grep -q 'systemctl enable nexus-boot-ready.service' "$BOOT_HOOK"
if grep -q '^After=.*multi-user.target' "$BOOT_UNIT"; then
  echo "Boot readiness service must not order itself after multi-user.target" >&2
  exit 1
fi
grep -qx '^WantedBy=multi-user.target$' "$BOOT_UNIT"
if [ -e "$ROOT/includes/etc/systemd/system/multi-user.target.wants/nexus-boot-ready.service" ] || [ -L "$ROOT/includes/etc/systemd/system/multi-user.target.wants/nexus-boot-ready.service" ]; then
  echo "Do not ship a duplicate wants entry; live-build hook enables the service" >&2
  exit 1
fi
grep -q 'NEXUS_LIVE_BOOT_READY_V1' "$BOOT_MARKER"
if grep -q '020-unattended-grub.hook.binary' "$BUILD"; then
  echo "GRUB binary hook runs before grub.cfg generation; do not stage it" >&2
  exit 1
fi
if grep -q 'config/hooks/binary' "$BUILD"; then
  echo "Invalid binary hook directory; use config/hooks/live" >&2
  exit 1
fi
grep -q 'set timeout=3' "$BUILD"
grep -q 'config/bootloaders/grub-pc/grub.cfg' "$BUILD"
grep -q 'GRUB_TEMPLATE=' "$BUILD"
python3 -m py_compile "$CONTROL_CENTER" "$INSTALLER_PREVIEW" "$HORIZON" "$HORIZON_PANEL"
grep -q "^Name=Nexus Horizon Panel Preview$" "$HORIZON_PANEL_DESKTOP"
grep -q "^Name=Nexus Horizon$" "$HORIZON_DESKTOP"
grep -q "^Exec=/usr/local/bin/nexus-horizon$" "$HORIZON_DESKTOP"
grep -q "Super&gt;space" "$HORIZON_SHORTCUTS"
grep -q "/usr/local/bin/nexus-horizon" "$HORIZON_SHORTCUTS"
test -x "$ROOT/includes/usr/local/bin/nexus-horizon"
test -x "$ROOT/includes/usr/local/bin/nexus-agent"
test -s "$ROOT/includes/usr/share/backgrounds/nexus/horizon-aurora.svg"
sh -n "$ROOT/includes/usr/local/libexec/nexus-horizon-appearance"
grep -q "^Name=Nexus Installation Preview$" "$INSTALLER_DESKTOP"
grep -q "^Exec=python3 /opt/nexus/installer-preview.py$" "$INSTALLER_DESKTOP"
grep -q "from installer_inventory import capture_inventory" "$INSTALLER_PREVIEW"
grep -q "from installer_plan import plan_install" "$INSTALLER_PREVIEW"
grep -q "Installation is DISABLED in this preview" "$INSTALLER_PREVIEW"
grep -q "installer_plan.py installer_inventory.py installer_preflight.py local_model_diagnostics.py action_preview.py app_installer.py" "$BUILD"

for flag in '--distribution trixie' '--architectures amd64' '--binary-images iso-hybrid' '--debian-installer none' '--bootloader grub-efi' 'console=ttyS0,115200n8'; do
  grep -q -- "$flag" "$ROOT/auto/config"
done
for package in chromium unzip zenity pkexec aapt waydroid weston winbind cabextract winetricks fonts-liberation; do grep -qx "$package" "$OMNI_PACKAGES"; done
grep -q '^deb http://deb.debian.org/debian trixie-backports main contrib$' "$OMNI_ARCHIVE"
grep -q '050-enable-nexus-omnios-binfmt.hook.chroot' "$BUILD"
grep -q 'nexus-omniloader --register-binfmt' "$OMNI_UNIT"
grep -q 'nexus-omniloader %f' "$OMNI_DESKTOP"
grep -q 'trixie-backports.list.chroot' "$BUILD"
grep -q 'omnios.list.chroot' "$BUILD"
grep -q 'nexus-omniloader' "$BUILD"
grep -q 'wasmtime' "$BUILD"
grep -q 'nexus-omniloader' "$OMNI_STAGE"
grep -q 'cargo +nightly -Z bindeps build' "$OMNI_STAGE"
grep -q 'cargo +nightly -Z bindeps test' "$ROOT/../.github/workflows/nexus-iso-gate.yml"
grep -q 'image/runtime-smoke.sh' "$ROOT/../.github/workflows/nexus-iso-gate.yml"
grep -q -- '--archive-areas "main contrib non-free-firmware"' "$ROOT/auto/config"
grep -q 'wine32:i386 winbind cabextract winetricks fonts-liberation' "$ROOT/hooks/030-wine-multiarch.hook.chroot"
grep -q 'binder_linux' "$WAYDROID_PREFLIGHT"
grep -q 'systemctl enable waydroid-container.service' "$WAYDROID_HOOK"
grep -q "DllOverrides" "$WINE_OFFICE_PROFILE"
grep -q 'Name=Nexus Windows Office Profile' "$ROOT/includes/usr/share/applications/nexus-wine-office-profile.desktop"
grep -q '040-waydroid-binder.hook.chroot' "$BUILD"

for module in nexus_agent.py provider_client.py conversation.py providers.py provider_catalog.py provider_diagnostics.py session.py capabilities.py router.py config.py secret_store.py linux_secret_store.py cli.py openai_compatible.py settings.py settings_store.py tool_broker.py system_tools.py file_grants.py permissions.py pe_inspector.py installer_plan.py installer_inventory.py installer_preflight.py local_model_diagnostics.py action_preview.py app_installer.py; do
  test -s "$PROJECT_ROOT/agent/$module" || { echo "Missing Nexus Agent runtime module: $module" >&2; exit 1; }
  python3 -m py_compile "$PROJECT_ROOT/agent/$module"
done

if grep -Eqi '(password|passwd|api[_-]?key|secret|token)[[:space:]]*=' "$BUILD" "$PACKAGES"; then
  echo "Potential embedded secret detected" >&2
  exit 1
fi
if grep -Eq -- '--debian-installer[[:space:]]+(live|true|netinst)' "$BUILD"; then
  echo "Installer unexpectedly enabled before safety gates" >&2
  exit 1
fi

if grep -Eq "sendkey|monitor stdio" "$ROOT/boot-smoke.sh"; then
  echo "Boot smoke test must not depend on synthetic keyboard input" >&2
  exit 1
fi

echo "Nexus OS image source checks passed"

test -s "$ROOT/includes/usr/share/applications/nexus-app-install.desktop"
grep -qx 'Exec=/usr/bin/python3 /opt/nexus/agent/app_installer.py %f' "$ROOT/includes/usr/share/applications/nexus-app-install.desktop"
grep -qx 'application/vnd.microsoft.portable-executable=nexus-app-install.desktop;' "$ROOT/includes/etc/skel/.config/mimeapps.list"

test -s "$ROOT/hooks/030-wine-multiarch.hook.chroot"
sh -n "$ROOT/hooks/030-wine-multiarch.hook.chroot"
grep -q '030-wine-multiarch.hook.chroot' "$BUILD"
grep -q 'application/vnd.microsoft.portable-executable=nexus-app-install.desktop;' "$ROOT/includes/etc/skel/.config/mimeapps.list"
for mime in application/vnd.android.package-archive application/x-msi application/x-mach-binary application/wasm application/x-chrome-extension application/vnd.debian.binary-package; do
  grep -q "^$mime=nexus-omnisubsystem.desktop;" "$ROOT/includes/etc/skel/.config/mimeapps.list"
done
