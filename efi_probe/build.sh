#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/efi_probe
clang --target=x86_64-pc-windows-msvc -fuse-ld=lld -nostdlib \
  -Wl,/entry:efi_main -Wl,/subsystem:efi_application -Wl,/nodefaultlib \
  -Wl,/machine:x64 -o build/efi_probe/BOOTX64.EFI efi_probe/boot.c
file build/efi_probe/BOOTX64.EFI
file build/efi_probe/BOOTX64.EFI | grep -Eq "PE32\\+ executable.*(EFI application|EFI \\(application\\))"
test -s build/efi_probe/BOOTX64.EFI
