#!/usr/bin/env bash
set -euo pipefail

ISO="${1:-}"
if [ -z "$ISO" ] || [ ! -f "$ISO" ]; then
  echo "Usage: $0 /path/to/nexus.iso" >&2
  exit 2
fi

command -v qemu-system-x86_64 >/dev/null || {
  echo "qemu-system-x86_64 is required" >&2
  exit 2
}

OVMF=""
for candidate in /usr/share/OVMF/OVMF_CODE.fd /usr/share/ovmf/OVMF.fd; do
  if [ -r "$candidate" ]; then
    OVMF="$candidate"
    break
  fi
done
if [ -z "$OVMF" ]; then
  echo "Readable OVMF firmware was not found" >&2
  exit 2
fi

TIMEOUT="${NEXUS_BOOT_TIMEOUT:-90}"
LOG="${NEXUS_BOOT_LOG:-nexus-qemu-serial.log}"
DEBUG_LOG="${NEXUS_QEMU_DEBUG_LOG:-nexus-qemu-debug.log}"
rm -f "$LOG" "$DEBUG_LOG"

set +e
timeout "$TIMEOUT" qemu-system-x86_64 \
  -machine q35,accel=tcg -m 2048 -smp 2 -boot d \
  -drive if=pflash,format=raw,readonly=on,file="$OVMF" \
  -cdrom "$ISO" -display none -serial "file:$LOG" \
  -monitor none -no-reboot -snapshot -D "$DEBUG_LOG" -d guest_errors,unimp
STATUS=$?
set -e

if [ "$STATUS" -ne 0 ] && [ "$STATUS" -ne 124 ]; then
  echo "QEMU failed with status $STATUS" >&2
  exit 1
fi

test -s "$LOG" || {
  echo "No serial boot evidence was captured" >&2
  exit 1
}

if ! grep -Fq "NEXUS_LIVE_BOOT_READY_V1" "$LOG"; then
  echo "Guest did not emit Nexus live readiness marker; boot gate FAILED" >&2
  echo "Serial log bytes: $(wc -c < "$LOG")" >&2
  tail -n 80 "$LOG" >&2 || true
  tail -n 40 "$DEBUG_LOG" >&2 || true
  exit 1
fi

echo "Nexus live guest readiness marker verified at $LOG"
echo "This verifies guest multi-user boot, not graphical login or installer readiness."
