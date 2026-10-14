#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$ROOT/.." && pwd)"
WORK="$ROOT/work"

for module in nexus_agent.py provider_client.py conversation.py providers.py session.py capabilities.py router.py config.py secrets.py cli.py openai_compatible.py; do
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

lb config --mode debian --distribution trixie --architectures amd64 --binary-images iso-hybrid --debian-installer none --archive-areas "main non-free-firmware" --bootappend-live "boot=live components"

mkdir -p config/package-lists
cp "$ROOT/desktop.list.chroot" config/package-lists/nexus-desktop.list.chroot

mkdir -p config/includes.chroot
cp -a "$ROOT/includes/." config/includes.chroot/

mkdir -p config/includes.chroot/opt/nexus/agent
for module in nexus_agent.py provider_client.py conversation.py providers.py session.py capabilities.py router.py config.py secrets.py cli.py openai_compatible.py; do
  cp "$PROJECT_ROOT/agent/$module" config/includes.chroot/opt/nexus/agent/
done

if [ "${NEXUS_PREPARE_ONLY:-0}" = "1" ]; then
  echo "Nexus image staging prepared; no ISO was built"
  exit 0
fi

lb build

test -n "$(find . -maxdepth 1 -name '*.iso' -print -quit)"
sha256sum ./*.iso > SHA256SUMS
