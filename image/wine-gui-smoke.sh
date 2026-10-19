#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOADER="${1:-$SCRIPT_DIR/staging/usr/bin/nexus-omniloader}"
APK="${2:-}"
CRX="${3:-}"
WASM="${4:-}"
IPA="${5:-}"

if [[ "${NEXUS_WINE_GUI_SESSION:-0}" != "1" ]]; then
  test -x "$LOADER" || { echo "nexus-omniloader is missing: $LOADER" >&2; exit 1; }
  for fixture in "$APK" "$CRX" "$WASM" "$IPA"; do
    test -s "$fixture" || { echo "Required visual smoke fixture is missing: $fixture" >&2; exit 1; }
  done
  if [[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]]; then
    NEXUS_WINE_GUI_SESSION=1 xvfb-run -a -s '-screen 0 1920x1080x24' \
      "$0" "$LOADER" "$APK" "$CRX" "$WASM" "$IPA"
  else
    NEXUS_WINE_GUI_SESSION=1 dbus-run-session -- \
      xvfb-run -a -s '-screen 0 1920x1080x24' \
      "$0" "$LOADER" "$APK" "$CRX" "$WASM" "$IPA"
  fi
  exit $?
fi

test -n "${DISPLAY:-}" || { echo "Xvfb did not set DISPLAY" >&2; exit 1; }
test -n "${DBUS_SESSION_BUS_ADDRESS:-}" || { echo "D-Bus session is missing" >&2; exit 1; }
command -v xfce4-session >/dev/null
command -v xdotool >/dev/null
command -v python3 >/dev/null
command -v "$LOADER" >/dev/null 2>&1 || test -x "$LOADER"
export PATH="$(dirname "$LOADER"):$PATH"

SESSION_ROOT="$(mktemp -d)"
export XDG_CONFIG_HOME="$SESSION_ROOT/config"
export XDG_CACHE_HOME="$SESSION_ROOT/cache"
export XDG_RUNTIME_DIR="$SESSION_ROOT/runtime"
mkdir -p "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_RUNTIME_DIR" \
  "$PROJECT_ROOT/evidence/windows" "$PROJECT_ROOT/evidence/android" "$PROJECT_ROOT/evidence/web" "$PROJECT_ROOT/evidence/ios"
chmod 0700 "$XDG_RUNTIME_DIR"
cp -a "$PROJECT_ROOT/image/includes/etc/skel/.config/." "$XDG_CONFIG_HOME/"

export WINEARCH=win64
export WINEPREFIX="$SESSION_ROOT/wine-prefix"
export WINEDEBUG=-all

xfce4-session > "$SESSION_ROOT/xfce-session.log" 2>&1 &
SESSION_PID=$!
APP_PID=""
SERVER_PID=""
cleanup() {
  if [ -n "$APP_PID" ]; then kill "$APP_PID" 2>/dev/null || true; fi
  if [ -n "$SERVER_PID" ]; then kill "$SERVER_PID" 2>/dev/null || true; fi
  if command -v wineserver >/dev/null 2>&1; then
    WINEPREFIX="$WINEPREFIX" wineserver -k >/dev/null 2>&1 || true
    timeout 15s env WINEPREFIX="$WINEPREFIX" wineserver -w >/dev/null 2>&1 || true
  fi
  kill "$SESSION_PID" 2>/dev/null || true
  wait "$SESSION_PID" 2>/dev/null || true
  rm -rf "$SESSION_ROOT"
}
trap cleanup EXIT

ready=0
for attempt in $(seq 1 60); do
  if xfconf-query -c xfce4-desktop -l 2>/dev/null | grep -q '/last-image$'; then
    ready=1
    break
  fi
  sleep 1
done
if [ "$ready" -ne 1 ]; then
  cat "$SESSION_ROOT/xfce-session.log" >&2 || true
  echo "XFCE desktop session did not initialize" >&2
  exit 1
fi

/bin/sh "$PROJECT_ROOT/image/includes/usr/local/libexec/nexus-horizon-appearance"
dbus-update-activation-environment DISPLAY XAUTHORITY XDG_CONFIG_HOME XDG_CACHE_HOME
sleep 2

# Capture the Windows PE GUI first: this is Wine's bundled Notepad dispatched by Nexus.
NOTEPAD="$(find /usr/lib -type f -iname notepad.exe -print -quit 2>/dev/null || true)"
test -n "$NOTEPAD" && test -f "$NOTEPAD" || {
  echo "Wine's bundled notepad.exe was not found" >&2
  exit 1
}
file "$NOTEPAD" | grep -Eq 'PE32\+? executable' || {
  echo "Wine notepad.exe is not a recognized PE executable: $NOTEPAD" >&2
  exit 1
}
"$LOADER" "$NOTEPAD" > "$SESSION_ROOT/notepad.log" 2>&1 &
APP_PID=$!
window_id=""
for attempt in $(seq 1 60); do
  window_id="$(xdotool search --onlyvisible --name '[Nn]otepad' 2>/dev/null | head -n 1 || true)"
  if [ -n "$window_id" ]; then break; fi
  sleep 1
done
if [ -z "$window_id" ]; then
  cat "$SESSION_ROOT/notepad.log" >&2 || true
  echo "Wine Notepad did not open a visible GUI window" >&2
  exit 1
fi
xdotool windowmove "$window_id" 320 180 2>/dev/null || true
xdotool windowsize "$window_id" 1000 700 2>/dev/null || true
sleep 3
capture_desktop() {
  python3 - "$1" <<'PY'
import os
import sys
from pathlib import Path
from PIL import ImageGrab

image = ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).convert("RGB")
if image.size != (1920, 1080):
    raise RuntimeError(f"Unexpected Xvfb desktop size: {image.size}")
path = Path(sys.argv[1])
image.save(path, format="PNG")
if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
    raise RuntimeError("Desktop capture was not written as PNG")
print(f"Captured XFCE desktop evidence: {path} ({image.width}x{image.height})")
PY
  test -s "$1"
}
capture_desktop "$PROJECT_ROOT/evidence/windows/wine-gui-running.png"
xdotool windowclose "$window_id" 2>/dev/null || true
NOTEPAD_PID="$APP_PID"
APP_PID=""
WINEPREFIX="$WINEPREFIX" wineserver -k >/dev/null 2>&1 || true
wait "$NOTEPAD_PID" 2>/dev/null || true

# Ask the dispatcher to inspect the Android APK, CRX, and WASI fixtures.
APK_REPORT="$("$LOADER" --inspect-apk "$APK")"
CRX_REPORT="$("$LOADER" --inspect-crx "$CRX")"
"$LOADER" "$WASM"
WASM_REPORT="nexus-omniloader dispatched the WASI module to Wasmtime; exit code 0."

# Use the native Nexus Cyber-Glass GTK launcher for visual evidence. Chromium is
# intentionally excluded from this Xvfb path because it is unstable in CI.
show_native_panel() {
  local ecosystem="$1" title="$2" status="$3" message="$4" fixture="$5" screenshot="$6" log="$7"
  python3 "$PROJECT_ROOT/image/includes/usr/lib/nexus/nexus-omniloader-ui.py" \
    --ecosystem "$ecosystem" --title "$title" --status "$status" --message "$message" --path "$fixture" \
    > "$log" 2>&1 &
  APP_PID=$!
  local window=""
  for attempt in $(seq 1 60); do
    window="$(xdotool search --onlyvisible --name "$title" 2>/dev/null | head -n 1 || true)"
    [ -n "$window" ] && break
    if ! kill -0 "$APP_PID" 2>/dev/null; then break; fi
    sleep 1
  done
  if [ -z "$window" ]; then
    cat "$log" >&2 || true
    echo "Nexus Cyber-Glass response window did not appear: $title" >&2
    kill "$APP_PID" 2>/dev/null || true
    wait "$APP_PID" 2>/dev/null || true
    APP_PID=""
    return 1
  fi
  xdotool windowmove "$window" 520 300 2>/dev/null || true
  sleep 2
  capture_desktop "$screenshot"
  xdotool windowclose "$window" 2>/dev/null || true
  wait "$APP_PID" || { cat "$log" >&2; return 1; }
  APP_PID=""
}

APK_PANEL_MESSAGE="$(printf 'This CI fixture is structural; it was not installed or executed.\n\n%s' "$APK_REPORT")"
CRX_PANEL_MESSAGE="$(printf 'Unsigned CRX fixture inspected; it was not installed.\n\n%s\n\n%s' "$CRX_REPORT" "$WASM_REPORT")"
show_native_panel "Android · APK" "Android APK response" "STRUCTURE VERIFIED · NOT EXECUTED" \
  "$APK_PANEL_MESSAGE" "$APK" "$PROJECT_ROOT/evidence/android/apk-running.png" "$SESSION_ROOT/android-panel.log"
show_native_panel "ChromeOS · CRX · WASI" "Web PWA" "CRX VERIFIED · PWA RESPONSE" \
  "$CRX_PANEL_MESSAGE" "$CRX" "$PROJECT_ROOT/evidence/web/crx-pwa-running.png" "$SESSION_ROOT/web-panel.log"

# Launch only the package inspector; iOS ARM64 code is not executed on Linux.
IOS_REPORT="$("$LOADER" --inspect-ipa "$IPA")"
grep -Fq 'com.example.nexus.iossmoke' <<< "$IOS_REPORT"
"$LOADER" "$IPA" > "$SESSION_ROOT/ios-ipa.log" 2>&1 &
APP_PID=$!
ios_window=""
for attempt in $(seq 1 60); do
  ios_window="$(xdotool search --onlyvisible --name 'Nexus iOS IPA response' 2>/dev/null | head -n 1 || true)"
  [ -n "$ios_window" ] && break
  sleep 1
done
if [ -z "$ios_window" ]; then
  cat "$SESSION_ROOT/ios-ipa.log" >&2 || true
  echo "iOS IPA inspection response did not open a visible XFCE window" >&2
  exit 1
fi
xdotool windowmove "$ios_window" 520 300 2>/dev/null || true
sleep 2
capture_desktop "$PROJECT_ROOT/evidence/ios/ipa-running.png"
xdotool windowactivate --sync "$ios_window" 2>/dev/null || true
xdotool key Return 2>/dev/null || true
wait "$APP_PID" || { cat "$SESSION_ROOT/ios-ipa.log" >&2; exit 1; }
APP_PID=""

echo "iOS IPA inspection response captured over XFCE; structural fixture was not executed."
