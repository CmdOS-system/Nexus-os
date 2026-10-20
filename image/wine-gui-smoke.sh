#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOADER="${1:-$SCRIPT_DIR/staging/usr/bin/nexus-omniloader}"
SEVENZIP_GUI="${2:?installed 7-Zip File Manager executable is required}"
test -x "$LOADER"
for tool in xfwm4 xdotool python3 ffmpeg ffprobe; do
  command -v "$tool" >/dev/null || { echo "Missing GUI evidence dependency: $tool" >&2; exit 1; }
done

SESSION_ROOT="$(mktemp -d)"
export HOME="${HOME:-$SESSION_ROOT/home}"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$SESSION_ROOT/config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$SESSION_ROOT/cache}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-$SESSION_ROOT/runtime}"
mkdir -p "$HOME" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_RUNTIME_DIR" \
  "$PROJECT_ROOT/evidence/windows" "$PROJECT_ROOT/evidence/web"
chmod 0700 "$XDG_RUNTIME_DIR"
export WINEARCH="${WINEARCH:-win64}" WINEDEBUG=-all
export NEXUS_RUNTIME_SMOKE="$SCRIPT_DIR/runtime-smoke.sh"
WM_PID=""
RECORDER_PID=""
cleanup() {
  trap - EXIT INT TERM
  [[ -z "$RECORDER_PID" ]] || { kill -INT "$RECORDER_PID" 2>/dev/null || true; wait "$RECORDER_PID" 2>/dev/null || true; }
  [[ -z "$WM_PID" ]] || { kill -TERM "$WM_PID" 2>/dev/null || true; wait "$WM_PID" 2>/dev/null || true; }
  if command -v wineserver >/dev/null 2>&1; then WINEPREFIX="${WINEPREFIX:-}" wineserver -k >/dev/null 2>&1 || true; fi
  rm -rf -- "$SESSION_ROOT"
}
trap cleanup EXIT

recorded_store_run() {
  local ecosystem="$1" app_id="$2" title="$3" package="$4" video="$5" primary="$6"
  mkdir -p "$(dirname "$video")"
  NO_AT_BRIDGE=1 xfwm4 --replace --compositor=off </dev/null >/dev/null 2>&1 &
  WM_PID=$!
  sleep 0.3
  bash -c 'trap - INT; exec ffmpeg -nostdin -hide_banner -loglevel error -y \
    -f x11grab -video_size 1280x720 -framerate 15 -i "$DISPLAY" -t 30 -an \
    -c:v libx264 -preset ultrafast -pix_fmt yuv420p -movflags +faststart "$1"' \
    _ "$video" </dev/null >/dev/null 2>&1 &
  RECORDER_PID=$!
  sleep 0.3
  python3 "$SCRIPT_DIR/tests/runtime/real-app-evidence.py" "$ecosystem" "$app_id" \
    "$PROJECT_ROOT/evidence/$ecosystem/${ecosystem}-installing.png" \
    "$PROJECT_ROOT/evidence/$ecosystem/${ecosystem}-interacting.png" "$title" "$package"
  cp "$PROJECT_ROOT/evidence/$ecosystem/${ecosystem}-interacting.png" "$primary"
  kill -INT "$RECORDER_PID" 2>/dev/null || true
  sleep 1
  wait "$RECORDER_PID" 2>/dev/null || true
  RECORDER_PID=""
  ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height \
    -of csv=p=0 "$video" | grep -Fxq 'h264,1280,720'
  kill -TERM "$WM_PID" 2>/dev/null || true
  wait "$WM_PID" 2>/dev/null || true
  WM_PID=""
}

if [[ "${NEXUS_REAL_GUI_SESSION:-0}" != "1" ]]; then
  if [[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]]; then
    NEXUS_REAL_GUI_SESSION=1 xvfb-run -a -s '-screen 0 1280x720x24 -nolisten tcp' bash "$0" "$LOADER" "$SEVENZIP_GUI"
  else
    NEXUS_REAL_GUI_SESSION=1 dbus-run-session -- xvfb-run -a -s '-screen 0 1280x720x24 -nolisten tcp' bash "$0" "$LOADER" "$SEVENZIP_GUI"
  fi
  exit $?
fi

test -n "${DISPLAY:-}" && test -n "${DBUS_SESSION_BUS_ADDRESS:-}"
recorded_store_run windows 7zip "7-Zip" "" \
  "$PROJECT_ROOT/evidence/windows/wine-gui-running.mp4" \
  "$PROJECT_ROOT/evidence/windows/wine-gui-running.png"
recorded_store_run web 2048-web "2048" "" \
  "$PROJECT_ROOT/evidence/web/crx-pwa-running.mp4" \
  "$PROJECT_ROOT/evidence/web/crx-pwa-running.png"
