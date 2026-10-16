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
CONTROL_DESKTOP="$ROOT/includes/usr/share/applications/nexus-control-center.desktop"
INSTALLER_PREVIEW="$ROOT/includes/opt/nexus/installer-preview.py"
INSTALLER_DESKTOP="$ROOT/includes/usr/share/applications/nexus-installer-preview.desktop"

bash -n "$ROOT/validate.sh"
bash -n "$BUILD"
bash -n "$LAUNCHER"
bash -n "$BOOT_HOOK"
sh -n "$GRUB_HOOK"
bash -n "$BOOT_MARKER"

for file in "$PACKAGES" "$IDENTITY" "$LAUNCHER" "$DESKTOP" "$BOOT_UNIT" "$BOOT_HOOK" "$GRUB_HOOK" "$BOOT_MARKER" "$CONTROL_CENTER" "$CONTROL_DESKTOP" "$INSTALLER_PREVIEW" "$INSTALLER_DESKTOP"; do
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
python3 -m py_compile "$CONTROL_CENTER" "$INSTALLER_PREVIEW"
grep -q "^Name=Nexus Installation Preview$" "$INSTALLER_DESKTOP"
grep -q "^Exec=python3 /opt/nexus/installer-preview.py$" "$INSTALLER_DESKTOP"
grep -q "from installer_inventory import capture_inventory" "$INSTALLER_PREVIEW"
grep -q "from installer_plan import plan_install" "$INSTALLER_PREVIEW"
grep -q "Installation is DISABLED in this preview" "$INSTALLER_PREVIEW"
grep -q "installer_plan.py installer_inventory.py installer_preflight.py local_model_diagnostics.py action_preview.py" "$BUILD"

for flag in '--distribution trixie' '--architectures amd64' '--binary-images iso-hybrid' '--debian-installer none' '--bootloader grub-efi' 'console=ttyS0,115200n8'; do
  grep -q -- "$flag" "$BUILD"
done

for module in nexus_agent.py provider_client.py conversation.py providers.py provider_catalog.py provider_diagnostics.py session.py capabilities.py router.py config.py secret_store.py linux_secret_store.py cli.py openai_compatible.py settings.py settings_store.py tool_broker.py system_tools.py file_grants.py permissions.py pe_inspector.py installer_plan.py installer_inventory.py installer_preflight.py local_model_diagnostics.py action_preview.py; do
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
