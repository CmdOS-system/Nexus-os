#!/usr/bin/env bash
# Human-observed XFCE smoke test. This is not an automated graphical pass gate.
set -euo pipefail
ISO="${1:-}"
if [[ -z "$ISO" || ! -f "$ISO" ]]; then
  echo "Usage: $0 /path/to/nexus.iso" >&2
  exit 2
fi
for cmd in qemu-system-x86_64 timeout; do
  command -v "$cmd" >/dev/null || { echo "Missing dependency: $cmd" >&2; exit 2; }
done
OVMF=""
for candidate in /usr/share/OVMF/OVMF_CODE.fd /usr/share/ovmf/OVMF.fd; do
  if [[ -r "$candidate" ]]; then OVMF="$candidate"; break; fi
done
[[ -n "$OVMF" ]] || { echo "OVMF firmware not found" >&2; exit 2; }
TIMEOUT="${NEXUS_GUI_TIMEOUT:-300}"
[[ "$TIMEOUT" =~ ^[1-9][0-9]*$ ]] || { echo "NEXUS_GUI_TIMEOUT must be a positive integer" >&2; exit 2; }
echo "Open a VNC client at 127.0.0.1:5901 and inspect the XFCE login and desktop."
echo "This diagnostic is MANUAL and does not prove a graphical session by itself."
set +e
timeout "$TIMEOUT" qemu-system-x86_64 \
  -machine q35,accel=tcg -m 2048 -smp 2 -boot d \
  -drive if=pflash,format=raw,readonly=on,file="$OVMF" \
  -cdrom "$ISO" -display none -vnc 127.0.0.1:1 \
  -serial file:nexus-gui-serial.log -monitor none -no-reboot -snapshot
status=$?
set -e
if [[ "$status" -ne 0 && "$status" -ne 124 ]]; then
  echo "QEMU failed with status $status" >&2
  exit 1
fi
echo "Manual inspection window ended. Record whether XFCE login and desktop actually worked."
