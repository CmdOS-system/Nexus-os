#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOADER="${1:-$SCRIPT_DIR/staging/usr/bin/nexus-omniloader}"
WIN32_APP="${2:?compiled Win32 GUI executable is required}"
WEBAPP="${3:?built PWA directory is required}"

if [[ "${NEXUS_REAL_GUI_SESSION:-0}" != "1" ]]; then
  if [[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]]; then
    NEXUS_REAL_GUI_SESSION=1 xvfb-run -a -s '-screen 0 1920x1080x24' \
      bash "$0" "$LOADER" "$WIN32_APP" "$WEBAPP"
  else
    NEXUS_REAL_GUI_SESSION=1 dbus-run-session -- \
      xvfb-run -a -s '-screen 0 1920x1080x24' \
      bash "$0" "$LOADER" "$WIN32_APP" "$WEBAPP"
  fi
  exit $?
fi

test -n "${DISPLAY:-}" || { echo "Xvfb did not set DISPLAY" >&2; exit 1; }
test -n "${DBUS_SESSION_BUS_ADDRESS:-}" || { echo "D-Bus session is missing" >&2; exit 1; }
test -x "$LOADER"
test -s "$WIN32_APP"
test -s "$WEBAPP/index.html"
for tool in xfce4-session xdotool python3 curl; do
  command -v "$tool" >/dev/null || { echo "Missing GUI smoke dependency: $tool" >&2; exit 1; }
done

SESSION_ROOT="$(mktemp -d)"
export HOME="$SESSION_ROOT/home"
export XDG_CONFIG_HOME="$SESSION_ROOT/config"
export XDG_CACHE_HOME="$SESSION_ROOT/cache"
export XDG_RUNTIME_DIR="$SESSION_ROOT/runtime"
mkdir -p "$HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_RUNTIME_DIR" \
  "$PROJECT_ROOT/evidence/boot" "$PROJECT_ROOT/evidence/windows" "$PROJECT_ROOT/evidence/web"
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
  if [[ -n "$APP_PID" ]]; then kill "$APP_PID" 2>/dev/null || true; fi
  if [[ -n "$SERVER_PID" ]]; then kill "$SERVER_PID" 2>/dev/null || true; fi
  if command -v wineserver >/dev/null 2>&1; then
    WINEPREFIX="$WINEPREFIX" wineserver -k >/dev/null 2>&1 || true
    timeout 15s env WINEPREFIX="$WINEPREFIX" wineserver -w >/dev/null 2>&1 || true
  fi
  kill "$SESSION_PID" 2>/dev/null || true
  wait "$SESSION_PID" 2>/dev/null || true
  rm -rf -- "$SESSION_ROOT"
}
trap cleanup EXIT

ready=0
for attempt in $(seq 1 20); do
  if xfconf-query -c xfce4-desktop -l 2>/dev/null | grep -q '/last-image$'; then
    ready=1
    break
  fi
  sleep 0.5
done
if [[ "$ready" -ne 1 ]]; then
  cat "$SESSION_ROOT/xfce-session.log" >&2 || true
  echo "XFCE desktop session did not initialize" >&2
  exit 1
fi
/bin/sh "$PROJECT_ROOT/image/includes/usr/local/libexec/nexus-horizon-appearance"
dbus-update-activation-environment DISPLAY XAUTHORITY XDG_CONFIG_HOME XDG_CACHE_HOME
sleep 2

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
print(f"Captured live application window: {path} ({image.width}x{image.height})")
PY
  test -s "$1"
}

reap_app() {
  local pid="$1"
  if ! timeout 10s tail --pid="$pid" -f /dev/null 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
  fi
  wait "$pid" 2>/dev/null || true
}

# This is a freshly started target XFCE session, captured before any test app.
capture_desktop "$PROJECT_ROOT/evidence/boot/desktop-boot.png"

# Confirm Wine's bundled Notepad remains launchable, then capture our real app.
NOTEPAD="$(find /usr/lib -type f -iname notepad.exe -print -quit 2>/dev/null || true)"
test -n "$NOTEPAD" && test -f "$NOTEPAD" || {
  echo "Wine's bundled notepad.exe was not found" >&2
  exit 1
}
"$LOADER" "$NOTEPAD" > "$SESSION_ROOT/notepad.log" 2>&1 &
APP_PID=$!
notepad_window=""
for attempt in $(seq 1 20); do
  notepad_window="$(xdotool search --onlyvisible --name '[Nn]otepad' 2>/dev/null | head -n 1 || true)"
  [[ -n "$notepad_window" ]] && break
  sleep 0.5
done
[[ -n "$notepad_window" ]] || { cat "$SESSION_ROOT/notepad.log" >&2; exit 1; }
xdotool windowclose "$notepad_window" 2>/dev/null || true
reap_app "$APP_PID"
APP_PID=""

"$LOADER" "$WIN32_APP" > "$SESSION_ROOT/win32.log" 2>&1 &
APP_PID=$!
win_window=""
win_title=""
win_tick=0
for attempt in $(seq 1 20); do
  win_window="$(xdotool search --onlyvisible --name 'Nexus Win32 live app - tick' 2>/dev/null | head -n 1 || true)"
  if [[ -n "$win_window" ]]; then
    win_title="$(xdotool getwindowname "$win_window" 2>/dev/null || true)"
    if [[ "$win_title" =~ tick[[:space:]]([0-9]+) ]]; then
      win_tick="${BASH_REMATCH[1]}"
      (( win_tick >= 3 )) && break
    fi
  fi
  sleep 0.5
done
[[ -n "$win_window" && "$win_tick" -ge 3 ]] || {
  cat "$SESSION_ROOT/win32.log" >&2 || true
  echo "Native Win32 GUI did not advance its live timer" >&2
  exit 1
}
xdotool windowmove "$win_window" 420 250 2>/dev/null || true
sleep 1
capture_desktop "$PROJECT_ROOT/evidence/windows/wine-gui-running.png"
xdotool windowclose "$win_window" 2>/dev/null || true
reap_app "$APP_PID"
APP_PID=""
echo "MinGW Win32 GUI ran under Wine through nexus-omniloader; dynamic tick $win_tick was visible."

# Serve a real PWA in a visible Chromium window under Xvfb and require its
# WebAssembly-driven counter and Canvas output before capturing the page.
PORT=18943
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$WEBAPP" \
  > "$SESSION_ROOT/web-server.log" 2>&1 &
SERVER_PID=$!
for attempt in $(seq 1 20); do
  if curl -fsS "http://127.0.0.1:$PORT/" >/dev/null; then break; fi
  sleep 0.5
done
curl -fsS "http://127.0.0.1:$PORT/app.wasm" -o "$SESSION_ROOT/app.wasm"
cmp -s "$SESSION_ROOT/app.wasm" "$WEBAPP/app.wasm"
NODE_PATH="$RUNNER_TEMP/nexus-playwright/node_modules${NODE_PATH:+:$NODE_PATH}" \
  NEXUS_PWA_URL="http://127.0.0.1:$PORT/" \
  NEXUS_PWA_SCREENSHOT="$PROJECT_ROOT/evidence/web/crx-pwa-running.png" \
  timeout --kill-after=1s 10s node "$PROJECT_ROOT/image/tests/webapp/runtime-smoke.cjs"
echo "Real Chromium rendered Canvas and executed the live WebAssembly PWA in Xvfb."
