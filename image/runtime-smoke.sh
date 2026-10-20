#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOADER="${NEXUS_OMNILOADER:-$ROOT/staging/usr/bin/nexus-omniloader}"

# Store actions share this entry point so clicks and CI smoke runs pass through
# the same OmniLoader dispatcher. This mode exits before starting the test suite.
if [[ "${1:-}" == "--store-install" || "${1:-}" == "--store-open" ]]; then
  action="$1"; ecosystem="${2:?ecosystem required}"; target="${3:?package or app ID required}"
  case "$ecosystem" in windows|android|ios|web|linux) ;; *) echo "Unknown OmniStore ecosystem: $ecosystem" >&2; exit 2 ;; esac
  if [[ "$ecosystem" == "web" ]]; then
    target="${target#web:}"
    exec "$LOADER" --webapp "$target"
  fi
  if [[ "$ecosystem" == "windows" && "$target" == "7zip:auto" ]]; then
    if [[ "$action" == "--store-install" ]]; then
      cache_dir="${NEXUS_RUNTIME_CACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/nexus/omnistore}"
      installer="$cache_dir/7z2604-x64.exe"
      wine_prefix="${WINEPREFIX:-$HOME/.local/share/nexus/wine/omnistore}"
      mkdir -p "$cache_dir"
      if [[ ! -s "$wine_prefix/drive_c/Program Files/7-Zip/7zFM.exe" ]]; then
        curl -fL --retry 2 --connect-timeout 10 --max-time 60 \
          https://github.com/ip7z/7zip/releases/download/26.04/7z2604-x64.exe -o "$installer"
        WINEPREFIX="$wine_prefix" "$LOADER" "$installer" /S
      fi
      test -s "$wine_prefix/drive_c/Program Files/7-Zip/7zFM.exe"
      echo "7-Zip 26.04 installed from the official signed Windows installer."
      exit 0
    fi
    wine_prefix="${WINEPREFIX:-$HOME/.local/share/nexus/wine/omnistore}"
    exec env WINEPREFIX="$wine_prefix" "$LOADER" "$wine_prefix/drive_c/Program Files/7-Zip/7zFM.exe"
  fi
  if [[ "$target" == flatpak:* ]]; then
    app_id="${target#flatpak:}"
    if [[ "$action" == "--store-install" ]]; then exec "$LOADER" --install-flatpak "$app_id"; fi
    exec "$LOADER" --run-flatpak "$app_id"
  fi
  exec "$LOADER" "$target"
fi

# Keep a single D-Bus session for the Xvfb apps and screenshots.
if [[ "${NEXUS_RUNTIME_SESSION:-0}" != "1" && -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]]; then
  if command -v dbus-run-session >/dev/null 2>&1; then
    exec dbus-run-session -- env NEXUS_RUNTIME_SESSION=1 "$BASH" "$0" "$@"
  fi
  echo "[smoke] dbus-run-session unavailable; continuing with the current session" >&2
fi

PROJECT_ROOT="$(cd "$ROOT/.." && pwd)"
WASMTIME="$ROOT/staging/usr/bin/wasmtime"
TEMP="$(mktemp -d)"
export WINEPREFIX="${WINEPREFIX:-$TEMP/wine-prefix}"
export WINEARCH="${WINEARCH:-win64}"
# Background jobs can inherit SIGINT as ignored. Relay it to FFmpeg so it can
# close MP4 containers cleanly, while making encoding failures non-fatal.
REAL_FFMPEG="$(command -v ffmpeg 2>/dev/null || true)"
if [[ -n "$REAL_FFMPEG" ]]; then
  mkdir -p "$TEMP/ffmpeg-bin"
  cat > "$TEMP/ffmpeg-bin/ffmpeg" <<'FFMPEG_WRAPPER'
#!/usr/bin/python3
import os
import signal
import subprocess
import sys

def reset_child_sigint():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

process = subprocess.Popen(
    [os.environ["NEXUS_REAL_FFMPEG"], *sys.argv[1:]],
    preexec_fn=reset_child_sigint,
)
def relay_interrupt(_signum, _frame):
    try:
        process.send_signal(signal.SIGINT)
    except ProcessLookupError:
        pass

signal.signal(signal.SIGINT, relay_interrupt)
process.wait()
sys.exit(0)
FFMPEG_WRAPPER
  chmod +x "$TEMP/ffmpeg-bin/ffmpeg"
  export NEXUS_REAL_FFMPEG="$REAL_FFMPEG"
  export PATH="$TEMP/ffmpeg-bin:$PATH"
fi
ANDROID_HOME="${ANDROID_HOME:-/usr/local/lib/android/sdk}"
BUILD_TOOLS="$ANDROID_HOME/build-tools/35.0.0"
cleanup() {
  local status=$?
  trap - EXIT
  if [[ -n "${WINEPREFIX:-}" ]] && command -v wineserver >/dev/null 2>&1; then
    WINEPREFIX="$WINEPREFIX" wineserver -k >/dev/null 2>&1 || true
  fi
  rm -rf -- "$TEMP" || status=$?
  exit "$status"
}
trap cleanup EXIT

run_test() {
  local label="$1"; shift
  echo "[smoke] $label" >&2
  timeout --kill-after=1s 15s "$@"
}
run_recorded_test() {
  local label="$1" video="$2"; shift 2
  [[ -n "$video" && "$video" == *.mp4 ]] || {
    echo "Video evidence path must be a non-empty .mp4 filename: ${video:-<empty>}" >&2
    return 2
  }
  mkdir -p "$(dirname "$video")"
  echo "[smoke] $label" >&2
  local test_status=0
  timeout --kill-after=2s 300s xvfb-run -a -s '-screen 0 1280x720x24 -nolisten tcp' \
    bash -s -- "$video" "$@" <<'RECORDED_TEST' || test_status=$?
set -euo pipefail
video_file="$1"; shift
wm_pid=""
recorder_pid=""
stop_pid() {
  local pid="$1" attempt
  [[ -n "$pid" ]] || return 0
  kill -TERM "$pid" 2>/dev/null || true
  for attempt in $(seq 1 10); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.1
  done
  kill -KILL "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
}

finish_recorder() {
  local pid="$1" attempt
  [[ -n "$pid" ]] || return 0
  kill -INT "$pid" 2>/dev/null || true
  # Give FFmpeg time to write the MP4 trailer/moov atom after the clean interrupt.
  sleep 1
  for attempt in $(seq 1 40); do
    jobs -pr | grep -Fxq "$pid" || break
    sleep 0.1
  done
  if jobs -pr | grep -Fxq "$pid"; then
    kill -TERM "$pid" 2>/dev/null || true
    for attempt in $(seq 1 10); do
      jobs -pr | grep -Fxq "$pid" || break
      sleep 0.1
    done
  fi
  if jobs -pr | grep -Fxq "$pid"; then
    kill -KILL "$pid" 2>/dev/null || true
  fi
  wait "$pid" 2>/dev/null || true
}
cleanup_recording() {
  trap - EXIT
  if [[ -n "$recorder_pid" ]]; then
    finish_recorder "$recorder_pid" || true
  fi
  stop_pid "$wm_pid"
  pkill -TERM -u "$(id -u)" -x xfconfd 2>/dev/null || true
}
trap cleanup_recording EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
NO_AT_BRIDGE=1 xfwm4 --replace --compositor=off </dev/null >/dev/null 2>&1 &
wm_pid=$!
bash -c 'trap - INT; exec ffmpeg -nostdin -hide_banner -loglevel error -y \
  -f x11grab -video_size 1280x720 -framerate 15 -i "$DISPLAY" -an \
  -c:v libx264 -preset ultrafast -pix_fmt yuv420p -movflags +faststart "$1"' \
  _ "$video_file" </dev/null >/dev/null 2>&1 &
recorder_pid=$!
sleep 0.3
"$@"
RECORDED_TEST
  (( test_status == 0 )) || return "$test_status"
  if [[ -s "$video" ]] && command -v ffprobe >/dev/null 2>&1 && \
      ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height \
        -of csv=p=0 "$video" 2>/dev/null | grep -Fxq 'h264,1280,720'; then
    echo "[smoke] Video evidence saved: $video" >&2
  else
    echo "[smoke] Video capture unavailable; retaining the PNG evidence for $label" >&2
    rm -f -- "$video"
    if [[ "${NEXUS_REQUIRE_VIDEO:-0}" == "1" ]]; then
      echo "Required MP4 evidence was not produced: $video" >&2
      return 1
    fi
  fi
}

run_store_evidence() {
  local ecosystem="$1" app_id="$2" title="$3" package="${4:-}" video primary
  case "$ecosystem" in
    windows) video="wine-gui-running.mp4"; primary="wine-gui-running.png" ;;
    android) video="apk-running.mp4"; primary="apk-running.png" ;;
    ios) video="ipa-running.mp4"; primary="ipa-running.png" ;;
    web) video="crx-pwa-running.mp4"; primary="crx-pwa-running.png" ;;
    linux) video="linux-app-running.mp4"; primary="linux-app-running.png" ;;
    *) echo "Unknown evidence ecosystem: $ecosystem" >&2; return 2 ;;
  esac
  run_recorded_test "Nexus OmniStore $ecosystem install/open evidence" \
    "$PROJECT_ROOT/evidence/$ecosystem/$video" \
    env NO_AT_BRIDGE=1 NEXUS_RUNTIME_SMOKE="$ROOT/runtime-smoke.sh" python3 "$ROOT/tests/runtime/real-app-evidence.py" "$ecosystem" "$app_id" \
      "$PROJECT_ROOT/evidence/$ecosystem/$ecosystem-installing.png" \
      "$PROJECT_ROOT/evidence/$ecosystem/$ecosystem-interacting.png" "$title" "$package"
  cp "$PROJECT_ROOT/evidence/$ecosystem/$ecosystem-interacting.png" "$PROJECT_ROOT/evidence/$ecosystem/$primary"
}
for tool in python3 unzip zip gcc x86_64-w64-mingw32-gcc xvfb-run node xfwm4 xdotool curl; do
  command -v "$tool" >/dev/null || { echo "Required runtime smoke tool missing: $tool" >&2; exit 1; }
done
# adb, emulator, scrcpy, Flatpak, and Android SDK commands are optional capabilities.
test -x "$LOADER" && test -x "$WASMTIME"
export NEXUS_SUBSYSTEM_HELPER="$ROOT/staging/usr/lib/nexus"
export NEXUS_SOUND_DISABLED=1
command -v wine64 >/dev/null || test -x /usr/lib/wine/wine64 || { echo "wine64 is required" >&2; exit 1; }

# Verify the real F-Droid APK when Android SDK tools are available.
# ISO Gate does not need adb, a device, or a full Android emulator.
if [[ -x "$BUILD_TOOLS/apksigner" ]]; then
  APK="$TEMP/privacyfriendly2048.apk"
  run_test "Download F-Droid 2048 APK" curl -fL --retry 2 --connect-timeout 10 --max-time 60 \
    https://f-droid.org/repo/org.secuso.privacyfriendly2048_100.apk -o "$APK"
  run_test "Verify F-Droid APK signature" "$BUILD_TOOLS/apksigner" verify --verbose "$APK"
  if [[ -x "$BUILD_TOOLS/aapt2" ]]; then
    run_test "Inspect F-Droid APK manifest" "$BUILD_TOOLS/aapt2" dump badging "$APK"
  fi
else
  echo "[smoke] Android SDK apksigner unavailable; skipping APK package inspection" >&2
fi
echo "[smoke] ISO Gate does not start an Android AVD; skipping adb/scrcpy UI capture and continuing lightweight runtime checks" >&2

# Keep a separate Wasmtime smoke check, then exercise the real 2048 PWA through OmniStore.
mkdir -p "$TEMP/webapp"
cp -a "$ROOT/tests/webapp/." "$TEMP/webapp/"
run_test "Build and execute WebAssembly smoke module" bash -c 'python3 "$1/tests/webapp/build_wasm.py" "$2/test.wasm" && test "$("$3" run --invoke advance "$2/test.wasm")" = 1' _ "$ROOT" "$TEMP" "$WASMTIME"
run_test "Compile PE exit smoke" x86_64-w64-mingw32-gcc -Os -static "$ROOT/tests/fixtures/pe-exit-zero.c" -o "$TEMP/pe-exit-zero.exe"
run_test "Execute PE exit smoke through Wine" bash -c 'xvfb-run -a "$1" "$2"' _ "$LOADER" "$TEMP/pe-exit-zero.exe"
WINEPREFIX="$WINEPREFIX" wineserver -k >/dev/null 2>&1 || true
timeout --kill-after=2s 300s bash "$ROOT/wine-gui-smoke.sh" "$LOADER" "7zip:auto" "$TEMP/webapp"
if command -v flatpak >/dev/null 2>&1; then
  run_store_evidence linux gnome-mines "Mines"
else
  echo "[smoke] Flatpak unavailable; skipping Flathub GNOME Mines evidence" >&2
fi
