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
command -v python3 >/dev/null || {
  echo "python3 is required for the QEMU screenshot" >&2
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
SCREENSHOT="${NEXUS_BOOT_SCREENSHOT:-evidence/boot/desktop-boot.png}"
SETTLE_SECONDS="${NEXUS_SCREENSHOT_SETTLE_SECONDS:-5}"
SCREENSHOT="$(realpath -m "$SCREENSHOT")"
mkdir -p "$(dirname "$SCREENSHOT")"
rm -f "$LOG" "$DEBUG_LOG"

TMP_DIR="$(mktemp -d)"
QMP_SOCKET="$TMP_DIR/qmp.sock"
PPM="$TMP_DIR/desktop.ppm"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

qemu_args=(
  -machine q35,accel=tcg
  -m 2048
  -smp 2
  -boot d
  -drive "if=pflash,format=raw,readonly=on,file=$OVMF"
  -cdrom "$ISO"
  -display vnc=127.0.0.1:0
  -serial "file:$LOG"
  -qmp "unix:$QMP_SOCKET,server=on,wait=off"
  -monitor none
  -no-reboot
  -snapshot
  -D "$DEBUG_LOG"
  -d guest_errors,unimp
)
for qemu_arg in "${qemu_args[@]}"; do
  if [[ -z "$qemu_arg" || "$qemu_arg" == *\\* ]]; then
    echo "Invalid empty or backslash-containing QEMU argument: [$qemu_arg]" >&2
    exit 2
  fi
done

timeout "$TIMEOUT" qemu-system-x86_64 "${qemu_args[@]}" &
QEMU_PID=$!

deadline=$((SECONDS + TIMEOUT))
READY=0
while (( SECONDS < deadline )); do
  if grep -Fq "NEXUS_XFCE_SESSION_READY_V1" "$LOG" 2>/dev/null; then
    READY=1
    break
  fi
  if ! kill -0 "$QEMU_PID" 2>/dev/null; then
    break
  fi
  sleep 1
done

if [ "$READY" -eq 1 ]; then
  # Give the XFCE panel and desktop compositor a moment to finish rendering.
  sleep "$SETTLE_SECONDS"
  python3 - "$QMP_SOCKET" "$PPM" "$SCREENSHOT" <<'PY'
import json
import socket
import struct
import sys
import time
import zlib
from pathlib import Path

socket_path, ppm_path, png_path = sys.argv[1:]
client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.settimeout(15)
deadline = time.monotonic() + 10
while True:
    try:
        client.connect(socket_path)
        break
    except (FileNotFoundError, ConnectionRefusedError):
        if time.monotonic() >= deadline:
            raise
        time.sleep(0.2)

stream = client.makefile("rwb", buffering=0)
greeting = json.loads(stream.readline())
if "QMP" not in greeting:
    raise RuntimeError("QEMU did not send a QMP greeting")

def qmp(command, arguments=None, expect_reply=True):
    message = {"execute": command}
    if arguments is not None:
        message["arguments"] = arguments
    stream.write((json.dumps(message) + "\r\n").encode())
    if not expect_reply:
        return
    while True:
        response = json.loads(stream.readline())
        if "error" in response:
            raise RuntimeError(f"QMP {command} failed: {response['error']}")
        if "return" in response:
            return response["return"]

qmp("qmp_capabilities")
qmp("screendump", {"filename": ppm_path})
qmp("quit", expect_reply=False)
client.close()

data = Path(ppm_path).read_bytes()
offset = 0

def token():
    global offset
    while offset < len(data):
        if data[offset] in b" \t\r\n":
            offset += 1
        elif data[offset] == ord("#"):
            newline = data.find(b"\n", offset)
            if newline < 0:
                raise ValueError("Malformed PPM comment")
            offset = newline + 1
        else:
            break
    start = offset
    while offset < len(data) and data[offset] not in b" \t\r\n#":
        offset += 1
    if start == offset:
        raise ValueError("Malformed PPM header")
    return data[start:offset]

if token() != b"P6":
    raise ValueError("QEMU screenshot is not a binary PPM image")
width, height, max_value = (int(token()) for _ in range(3))
if max_value != 255:
    raise ValueError(f"Unsupported PPM channel depth: {max_value}")
if data[offset:offset + 2] == b"\r\n":
    offset += 2
elif offset < len(data) and data[offset] in b" \t\r\n":
    offset += 1
else:
    raise ValueError("Malformed PPM pixel separator")
pixels = data[offset:]
row_bytes = width * 3
if len(pixels) != row_bytes * height:
    raise ValueError("QEMU PPM screenshot has an unexpected pixel-data size")

def chunk(kind, body):
    payload = kind + body
    return struct.pack(">I", len(body)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xffffffff)

raw = b"".join(b"\x00" + pixels[y * row_bytes:(y + 1) * row_bytes] for y in range(height))
png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(raw, 9))
       + chunk(b"IEND", b""))
Path(png_path).write_bytes(png)
print(f"Saved XFCE QEMU framebuffer screenshot: {png_path} ({width}x{height})")
PY
else
  echo "Guest did not reach a real XFCE user session before timeout" >&2
  tail -n 140 "$LOG" >&2 || true
  tail -n 40 "$DEBUG_LOG" >&2 || true
fi

set +e
wait "$QEMU_PID"
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

if ! grep -Fq "NEXUS_GRAPHICAL_STACK_READY_V1" "$LOG"; then
  echo "Guest reached multi-user boot but graphical stack readiness was not proven" >&2
  tail -n 120 "$LOG" >&2 || true
  exit 1
fi

if ! grep -Fq "NEXUS_XFCE_SESSION_READY_V1" "$LOG"; then
  echo "Graphical stack is active but a real XFCE user session was not proven" >&2
  tail -n 140 "$LOG" >&2 || true
  exit 1
fi

test -s "$SCREENSHOT" || {
  echo "XFCE desktop screenshot was not captured: $SCREENSHOT" >&2
  exit 1
}

echo "Nexus live, graphical-stack, and XFCE user-session readiness verified at $LOG"
echo "Saved clean XFCE desktop screenshot at $SCREENSHOT"
echo "This verifies a real XFCE session with DISPLAY and session D-Bus, captures its QEMU framebuffer, and does not yet prove installer readiness."
