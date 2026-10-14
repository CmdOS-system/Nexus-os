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
BOOT_MARKER="$ROOT/includes/usr/local/libexec/nexus-boot-ready"
CONTROL_CENTER="$ROOT/includes/opt/nexus/control-center.py"
CONTROL_DESKTOP="$ROOT/includes/usr/share/applications/nexus-control-center.desktop"

bash -n "$BUILD"
bash -n "$LAUNCHER"
bash -n "$BOOT_HOOK"
bash -n "$BOOT_MARKER"

for file in "$PACKAGES" "$IDENTITY" "$LAUNCHER" "$DESKTOP" "$BOOT_UNIT" "$BOOT_HOOK" "$BOOT_MARKER" "$CONTROL_CENTER" "$CONTROL_DESKTOP"; do
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
grep -q 'NEXUS_LIVE_BOOT_READY_V1' "$BOOT_MARKER"
python3 -m py_compile "$CONTROL_CENTER"

for flag in '--distribution trixie' '--architectures amd64' '--binary-images iso-hybrid' '--debian-installer none'; do
  grep -q -- "$flag" "$BUILD"
done

for module in nexus_agent.py provider_client.py conversation.py providers.py provider_catalog.py provider_diagnostics.py session.py capabilities.py router.py config.py secret_store.py linux_secret_store.py cli.py openai_compatible.py settings.py settings_store.py tool_broker.py system_tools.py file_grants.py permissions.py; do
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

echo "Nexus OS image source checks passed"
