#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD="$ROOT/build.sh"
PACKAGES="$ROOT/desktop.list.chroot"

bash -n "$BUILD"
test -s "$PACKAGES"

grep -qx 'task-xfce-desktop' "$PACKAGES"
grep -qx 'network-manager' "$PACKAGES"
grep -qx 'ca-certificates' "$PACKAGES"

grep -q -- '--distribution trixie' "$BUILD"
grep -q -- '--architectures amd64' "$BUILD"
grep -q -- '--binary-images iso-hybrid' "$BUILD"
grep -q -- '--debian-installer none' "$BUILD"

if grep -Eqi '(password|passwd|api[_-]?key|secret|token)[[:space:]]*=' "$BUILD" "$PACKAGES"; then
  echo "Potential embedded secret detected" >&2
  exit 1
fi

if grep -Eq -- '--debian-installer[[:space:]]+(live|true|netinst)' "$BUILD"; then
  echo "Installer unexpectedly enabled before safety gates" >&2
  exit 1
fi

echo "Nexus OS image source checks passed"
