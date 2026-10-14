#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash -n "$ROOT/build.sh"
grep -qx 'task-xfce-desktop' "$ROOT/desktop.list.chroot"
grep -qx 'network-manager' "$ROOT/desktop.list.chroot"
echo "Nexus OS image source checks passed"
