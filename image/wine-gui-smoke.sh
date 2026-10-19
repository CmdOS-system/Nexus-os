#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOADER="\${1:-$SCRIPT_DIR/staging/usr/bin/nexus-omniloader}"
NOTEPAD="\${2:-}"

if [[ "\${NEXUS_WINE_GUI_SESSION:-0}" != "1" ]]; then
  test -x "$LOADER" || { echo "nexus-omniloader is missing: $LOADER" >&2; exit 1; }
  if [ -z "$NOTEPAD" ]; then
    NOTEPAD="$(find /usr/lib -type f -iname notepad.exe -print -quit 2>/dev/null || true)"
  fi
  test -n "$NOTEPAD" && test -f "$NOTEPAD" || {
    echo "Wine's bundled notepad.exe was not found" >&2
    exit 1
  }
  file "$NOTEPAD" | grep -Eq 'PE32\+? executable' || {
    echo "Wine notepad.exe is not a recognized PE executable: $NOTEPAD" >&2
    exit 1
  }
  exec dbus-run-session -- xvfb-run -a -s '-screen 0 1920x1080x24' \
    env NEXUS_WINE_GUI_SESSION=1 "$0" "$LOADER" "$NOTEPAD"
fi

test -n "\${DISPLAY:-}" || { echo "Xvfb did not set DISPLAY" >&2; exit 1; }
test -n "\${DBUS_SESSION_BUS_ADDRESS:-}" || { echo "D-Bus session is missing" >&2; exit 1; }
command -v xfce4-session >/dev/null
command -v xdotool >/dev/null
command -v python3 >/dev/null

EVIDENCE="$PROJECT_ROOT/evidence/windows/wine-gui-running.png"
SESSION_ROOT="$(mktemp -d)"
export XDG_CONFIG_HOME="$SESSION_ROOT/config"
export XDG_CACHE_HOME="$SESSION_ROOT/cache"
export XDG_RUNTIME_DIR="$SESSION_ROOT/runtime"
mkdir -p "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_RUNTIME_DIR" "$(dirname "$EVIDENCE")"
chmod 0700 "$XDG_RUNTIME_DIR"
cp -a "$PROJECT_ROOT/image/includes/etc/skel/.config/." "$XDG_CONFIG_HOME/"

export WINEARCH=win64
export WINEPREFIX="$SESSION_ROOT/wine-prefix"
export WINEDEBUG=-all

xfce4-session > "$SESSION_ROOT/xfce-session.log" 2>&1 &
SESSION_PID=$!
APP_PID=""
cleanup() {
  if [ -n "$APP_PID" ]; then
    kill "$APP_PID" 2>/dev/null || true
  fi
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
dbus-update-activation-environment XDG_CONFIG_HOME XDG_CACHE_HOME
sleep 2

"$LOADER" "$NOTEPAD" > "$SESSION_ROOT/notepad.log" 2>&1 &
APP_PID=$!
window_id=""
for attempt in $(seq 1 60); do
  window_id="$(xdotool search --onlyvisible --name '[Nn]otepad' 2>/dev/null | head -n 1 || true)"
  if [ -n "$window_id" ]; then
    break
  fi
  if ! kill -0 "$APP_PID" 2>/dev/null; then
    break
  fi
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
python3 - "$EVIDENCE" <<'PY'
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
print(f"Captured Wine Notepad over the Nexus XFCE desktop: {path} ({image.width}x{image.height})")
PY
test -s "$EVIDENCE"
echo "Wine GUI smoke passed through nexus-omniloader."
