#!/usr/bin/env bash
set -euo pipefail

# Check desktop launchers without launching an untrusted GUI session.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INCLUDES="$ROOT/includes"
for desktop in nexus-agent nexus-control-center; do
  file="$INCLUDES/usr/share/applications/$desktop.desktop"
  test -s "$file" || { echo "Missing launcher: $file" >&2; exit 1; }
  grep -Fxq '[Desktop Entry]' "$file" || { echo "Invalid launcher: $file" >&2; exit 1; }
  grep -qx 'Type=Application' "$file" || exit 1
  grep -q '^Exec=' "$file" || exit 1
done

agent_exec="$(sed -n 's/^Exec=//p' "$INCLUDES/usr/share/applications/nexus-agent.desktop")"
control_exec="$(sed -n 's/^Exec=//p' "$INCLUDES/usr/share/applications/nexus-control-center.desktop")"
test "$agent_exec" = 'x-terminal-emulator -e /usr/local/bin/nexus-agent'
test "$control_exec" = 'python3 /opt/nexus/control-center.py'
test -s "$INCLUDES/usr/local/bin/nexus-agent"
test -s "$INCLUDES/opt/nexus/control-center.py"
python3 -m py_compile "$INCLUDES/opt/nexus/control-center.py"
echo "Nexus desktop launcher source checks passed"
