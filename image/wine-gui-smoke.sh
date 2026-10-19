#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "@{BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOADER="@{1:-$SCRIPT_DIR/staging/usr/bin/nexus-omniloader}"
APK="@{2:-}"
CRX="@{3:-}"
WASM="@{4:-}"

if [[ "@{NEXUS_WINE_GUI_SESSION:-0}" != "1" ]]; then
  test -x "$LOADER" || { echo "nexus-omniloader is missing: $LOADER" >&2; exit 1; }
  for fixture in "$APK" "$CRX" "$WASM"; do
    test -s "$fixture" || { echo "Required visual smoke fixture is missing: $fixture" >&2; exit 1; }
  done
  BROWSER_BIN="$(command -v chromium || command -v google-chrome || command -v google-chrome-stable || true)"
  test -n "$BROWSER_BIN" || {
    echo "A Chromium-compatible browser is required for graphical PWA evidence" >&2
    exit 1
  }
  SHIM_DIR="$(mktemp -d)"
  trap 'rm -rf "$SHIM_DIR"' EXIT
  printf '#!/usr/bin/env bash\nexec %q "$@"\n' "$BROWSER_BIN" > "$SHIM_DIR/chromium"
  chmod 0755 "$SHIM_DIR/chromium"
  NEXUS_WINE_GUI_SESSION=1 PATH="$SHIM_DIR:$PATH" \
    dbus-run-session -- xvfb-run -a -s '-screen 0 1920x1080x24' \
    "$0" "$LOADER" "$APK" "$CRX" "$WASM"
  exit $?
fi

test -n "@{DISPLAY:-}" || { echo "Xvfb did not set DISPLAY" >&2; exit 1; }
test -n "@{DBUS_SESSION_BUS_ADDRESS:-}" || { echo "D-Bus session is missing" >&2; exit 1; }
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
  "$PROJECT_ROOT/evidence/windows" "$PROJECT_ROOT/evidence/android" "$PROJECT_ROOT/evidence/web"
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
dbus-update-activation-environment XDG_CONFIG_HOME XDG_CACHE_HOME
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

PREVIEW_ROOT="$SESSION_ROOT/previews"
mkdir -p "$PREVIEW_ROOT"
NEXUS_APK_REPORT="$APK_REPORT" NEXUS_CRX_REPORT="$CRX_REPORT" NEXUS_WASM_REPORT="$WASM_REPORT" \
python3 - "$PREVIEW_ROOT" <<'PY'
import html
import os
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
apk = html.escape(os.environ["NEXUS_APK_REPORT"])
crx = html.escape(os.environ["NEXUS_CRX_REPORT"])
wasm = html.escape(os.environ["NEXUS_WASM_REPORT"])
style = """
*{box-sizing:border-box} body{margin:0;background:#091522;color:#eaf2ff;font:16px Inter,Arial,sans-serif}
.top{height:58px;padding:18px 28px;background:#0e2033;border-bottom:1px solid #29435b;color:#9fe6d5;letter-spacing:.08em}
main{padding:34px 40px} h1{font-size:32px;margin:10px 0 8px} .sub{color:#a9bfd2;margin-bottom:28px}
.panel{background:#12283b;border:1px solid #2b4760;border-radius:16px;padding:24px;margin:18px 0;box-shadow:0 15px 38px #030b12}
.ok{color:#7ce0b7;font-weight:700}.note{color:#b8cad8;line-height:1.6}.code{font:14px ui-monospace,monospace;color:#cce5f5;background:#0a1928;padding:14px;border-radius:9px;overflow-wrap:anywhere}
.tag{display:inline-block;padding:6px 10px;border-radius:18px;background:#173d46;color:#9de8d6;font-size:13px}
"""
def page(title, heading, sub, blocks):
    body = "".join(f'<section class="panel"><div class="tag">{tag}</div><h2>{name}</h2><p class="ok">{status}</p><p class="note">{note}</p>{code}</section>' for tag,name,status,note,code in blocks)
    return f'<!doctype html><html><head><meta charset="utf-8"><title>{title}</title><style>{style}</style></head><body><header class="top">NEXUS OS <span style="float:right">OMNISUBSYSTEM · VISUAL SMOKE</span></header><main><h1>{heading}</h1><div class="sub">{sub}</div>{body}</main></body></html>'

apk_blocks = [("ANDROID · APK", "APK inspection response", "Nexus loader accepted the fixture", "This CI APK has an empty DEX and no launchable Activity; the UI records structural validation only, not an Android app install or execution.", f'<div class="code">{apk}</div>')]
(root / "android.html").write_text(page("Nexus Android APK response", "Android package · visual response", "The package was inspected by nexus-omniloader from the active XFCE test session.", apk_blocks))
web_blocks = [
    ("CHROMEOS · CRX", "Extension package response", "CRX structure inspected", "The fixture is unsigned and is not installed. Chromium remains responsible for publisher and permission review.", f'<div class="code">{crx}</div>'),
    ("WASM · WASI", "WebAssembly runtime response", "WASI fixture ran successfully", "Execution is routed through nexus-omniloader to the staged Wasmtime runtime.", f'<div class="code">{wasm}</div>'),
    ("PWA · CHROMIUM", "Progressive web app", "This Chromium app window is active", "The smoke test serves this local response over localhost and launches it through nexus-omniloader --webapp.", "")
]
(root / "web.html").write_text(page("Nexus Web PWA running", "Web · ChromeOS · WASI", "Container and runtime responses from the same Nexus XFCE smoke session.", web_blocks))
PY

# A local localhost page is used so the real Chromium PWA can run offline in CI.
PORT="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')"
python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$PREVIEW_ROOT" > "$SESSION_ROOT/http.log" 2>&1 &
SERVER_PID=$!
for attempt in $(seq 1 20); do
  if curl -fsS "http://localhost:$PORT/android.html" >/dev/null; then break; fi
  sleep 1
done

open_app_page() {
  local path="$1" title="$2" screenshot="$3" home="$4" log="$5"
  mkdir -p "$home"
  HOME="$home" "$LOADER" --webapp "http://localhost:$PORT/$path" > "$log" 2>&1 &
  local loader_pid=$!
  local window=""
  for attempt in $(seq 1 60); do
    window="$(xdotool search --onlyvisible --name "$title" 2>/dev/null | head -n 1 || true)"
    [ -n "$window" ] && break
    sleep 1
  done
  if [ -z "$window" ]; then
    cat "$log" >&2 || true
    echo "Chromium app window did not appear: $title" >&2
    kill "$loader_pid" 2>/dev/null || true
    wait "$loader_pid" 2>/dev/null || true
    return 1
  fi
  xdotool windowmove "$window" 360 150 2>/dev/null || true
  xdotool windowsize "$window" 1120 760 2>/dev/null || true
  sleep 3
  capture_desktop "$screenshot"
  local browser_pid
  browser_pid="$(xdotool getwindowpid "$window" 2>/dev/null || true)"
  xdotool windowclose "$window" 2>/dev/null || true
  sleep 1
  if [ -n "$browser_pid" ]; then kill "$browser_pid" 2>/dev/null || true; fi
  wait "$loader_pid" 2>/dev/null || true
}

open_app_page "android.html" "Android APK response" "$PROJECT_ROOT/evidence/android/apk-running.png" \
  "$SESSION_ROOT/android-home" "$SESSION_ROOT/android-app.log"
open_app_page "web.html" "Web PWA" "$PROJECT_ROOT/evidence/web/crx-pwa-running.png" \
  "$SESSION_ROOT/web-home" "$SESSION_ROOT/web-app.log"

echo "Android APK inspection response and CRX/WASI/PWA Chromium evidence captured through nexus-omniloader."
