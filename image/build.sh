#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$ROOT/.." && pwd)"
WORK="$ROOT/work"

for module in nexus_agent.py provider_client.py conversation.py providers.py provider_catalog.py provider_diagnostics.py session.py capabilities.py router.py config.py secret_store.py linux_secret_store.py cli.py openai_compatible.py settings.py settings_store.py tool_broker.py system_tools.py file_grants.py permissions.py pe_inspector.py installer_plan.py installer_inventory.py; do
  test -s "$PROJECT_ROOT/agent/$module" || {
    echo "Missing Nexus Agent runtime module: $module" >&2
    exit 1
  }
done

if [ -L "$WORK" ]; then
  echo "Refusing symlinked work directory" >&2
  exit 1
fi
mkdir -p "$WORK"
cd "$WORK"

lb config --mode debian --distribution trixie --architectures amd64 --binary-images iso-hybrid --debian-installer none --archive-areas "main non-free-firmware" --bootloader grub-efi --bootappend-live "boot=live components console=tty0 console=ttyS0,115200n8"

mkdir -p config/bootloaders/grub-pc
GRUB_TEMPLATE="/usr/share/live/build/bootloaders/grub-pc/grub.cfg"
test -s "$GRUB_TEMPLATE" || { echo "Missing live-build GRUB template: $GRUB_TEMPLATE" >&2; exit 1; }
{
  printf "%s\n" "# Nexus OS: automatically boot the default live entry" "set default=0" "set timeout_style=menu" "set timeout=3"
  cat "$GRUB_TEMPLATE"
} > config/bootloaders/grub-pc/grub.cfg

mkdir -p config/package-lists
cp "$ROOT/desktop.list.chroot" config/package-lists/nexus-desktop.list.chroot

mkdir -p config/hooks/live
cp "$ROOT/hooks/010-enable-nexus-boot-ready.hook.chroot" config/hooks/live/
chmod 0755 config/hooks/live/010-enable-nexus-boot-ready.hook.chroot


mkdir -p config/includes.chroot
cp -a "$ROOT/includes/." config/includes.chroot/

mkdir -p config/includes.chroot/opt/nexus/agent
for module in nexus_agent.py provider_client.py conversation.py providers.py provider_catalog.py provider_diagnostics.py session.py capabilities.py router.py config.py secret_store.py linux_secret_store.py cli.py openai_compatible.py settings.py settings_store.py tool_broker.py system_tools.py file_grants.py permissions.py pe_inspector.py installer_plan.py installer_inventory.py; do
  cp "$PROJECT_ROOT/agent/$module" config/includes.chroot/opt/nexus/agent/
done

if [ "${NEXUS_PREPARE_ONLY:-0}" = "1" ]; then
  echo "Nexus image staging prepared; no ISO was built"
  exit 0
fi

lb build

test -n "$(find . -maxdepth 1 -name '*.iso' -print -quit)"
sha256sum ./*.iso > SHA256SUMS
