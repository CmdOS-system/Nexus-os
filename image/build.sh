#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$ROOT/work"
cd "$ROOT/work"
lb config --mode debian --distribution trixie --architectures amd64 --binary-images iso-hybrid --debian-installer none --archive-areas "main non-free-firmware" --bootappend-live "boot=live components"
mkdir -p config/package-lists
cp "$ROOT/desktop.list.chroot" config/package-lists/nexus-desktop.list.chroot
lb build
test -n "$(find . -maxdepth 1 -name '*.iso' -print -quit)"
sha256sum ./*.iso > SHA256SUMS
