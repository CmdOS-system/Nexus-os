#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$ROOT/.." && pwd)"
BUILD="$ROOT/build.sh"
PACKAGES="$ROOT/desktop.list.chroot"
IDENTITY="$ROOT/includes/etc/nexus-os-release"
LAUNCHER="$ROOT/includes/usr/local/bin/nexus-agent"
DESKTOP="$ROOT/includes/usr/share/applications/nexus-agent.desktop"

bash -n "$BUILD"
bash -n "$LAUNCHER"

for file in "$PACKAGES" "$IDENTITY" "$LAUNCHER" "$DESKTOP"; do
  test -s "$file" || { echo "Missing required image source: $file" >&2; exit 1; }
done

for package in task-xfce-desktop network-manager ca-certificates; do
  grep -qx "$package" "$PACKAGES"
done

grep -q 'NAME="Nexus OS"' "$IDENTITY"
grep -q '^ID=nexus$' "$IDENTITY"
grep -q '^ID_LIKE=debian$' "$IDENTITY"
grep -q '^Name=Nexus Agent$' "$DESKTOP"

for flag in '--distribution trixie' '--architectures amd64' '--binary-images iso-hybrid' '--debian-installer none'; do
  grep -q -- "$flag" "$BUILD"
done

for module in nexus_agent.py provider_client.py conversation.py providers.py session.py capabilities.py router.py config.py secrets.py cli.py openai_compatible.py settings.py tool_broker.py system_tools.py; do
  test -s "$PROJECT_ROOT/agent/$module" || {
    echo "Missing Nexus Agent runtime module: $module" >&2
    exit 1
  }
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
