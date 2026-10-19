#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APK="${1:?built Android APK is required}"
LOADER="${2:?built nexus-omniloader is required}"
OUT="$ROOT/evidence/android/apk-running.png"
mkdir -p "$(dirname "$OUT")"

adb wait-for-device
for attempt in $(seq 1 120); do
  [[ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]] && break
  sleep 2
done
[[ "$(adb shell getprop sys.boot_completed | tr -d '\r')" == "1" ]] || {
  echo "Android Emulator did not finish booting" >&2
  exit 1
}
adb shell input keyevent 82 || true
adb logcat -c
NEXUS_ANDROID_TARGET=adb NEXUS_SMOKE_AUTOCONFIRM=1 "$LOADER" "$APK"

frame=0
for attempt in $(seq 1 40); do
  frame="$(adb logcat -d -s NexusAndroid:I | sed -n 's/.*frame=\([0-9][0-9]*\).*/\1/p' | tail -n 1)"
  [[ "${frame:-0}" =~ ^[0-9]+$ ]] && (( frame >= 5 )) && break
  sleep 1
done
[[ "${frame:-0}" =~ ^[0-9]+$ && "$frame" -ge 5 ]] || {
  adb logcat -d -s NexusAndroid:E >&2 || true
  echo "Android Activity did not render its live DEX frame counter" >&2
  exit 1
}
adb exec-out screencap -p > "$OUT"
python3 - "$OUT" <<'PY'
import pathlib, sys
data = pathlib.Path(sys.argv[1]).read_bytes()
assert data.startswith(b"\x89PNG\r\n\x1a\n"), "Android Emulator screen capture is not PNG"
assert len(data) > 4_096, "Android Emulator capture looks empty"
PY
echo "Installed APK through nexus-omniloader and observed Android runtime frame $frame; screenshot: $OUT"
