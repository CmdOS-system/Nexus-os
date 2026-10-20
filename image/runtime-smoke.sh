#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOADER="${NEXUS_OMNILOADER:-$ROOT/staging/usr/bin/nexus-omniloader}"

# A Wine GUI from a previous Xvfb session can leave wineserver bound to that
# dead display. Kill the server for this exact prefix and bound the wait so a
# stuck wineserver can never hold the smoke test open indefinitely.
stop_wineserver() {
  local prefix="$1"
  WINEPREFIX="$prefix" wineserver -k >/dev/null 2>&1 || true
  timeout --kill-after=1s 10s env WINEPREFIX="$prefix" wineserver -w \
    >/dev/null 2>&1 || true
}

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
        timeout --kill-after=5s 60s env WINEPREFIX="$wine_prefix" "$LOADER" "$installer" /S
        stop_wineserver "$wine_prefix"
      fi
      sevenzip_exe="$wine_prefix/drive_c/Program Files/7-Zip/7zFM.exe"
      if [[ ! -s "$sevenzip_exe" ]]; then
        sevenzip_exe="$(find "$wine_prefix" -type f -iname '7zFM.exe' -print -quit 2>/dev/null || true)"
      fi
      if [[ -z "$sevenzip_exe" || ! -s "$sevenzip_exe" ]]; then
        extract_dir="$wine_prefix/drive_c/Program Files/7-Zip"
        mkdir -p "$extract_dir"
        if command -v 7z >/dev/null 2>&1; then
          timeout --kill-after=2s 30s 7z x "$installer" "-o$extract_dir" -y \
            >/dev/null 2>&1 || true
        fi
        sevenzip_exe="$(find "$wine_prefix" -type f -iname '7zFM.exe' -print -quit 2>/dev/null || true)"
      fi
      test -n "$sevenzip_exe" && test -s "$sevenzip_exe"
      echo "7-Zip 26.04 installed from the official signed Windows installer."
      exit 0
    fi
    wine_prefix="${WINEPREFIX:-$HOME/.local/share/nexus/wine/omnistore}"
    stop_wineserver "$wine_prefix"
    sevenzip_exe="$wine_prefix/drive_c/Program Files/7-Zip/7zFM.exe"
    if [[ ! -s "$sevenzip_exe" ]]; then
      sevenzip_exe="$(find "$wine_prefix" -type f -iname '7zFM.exe' -print -quit 2>/dev/null || true)"
    fi
    test -n "$sevenzip_exe" && test -s "$sevenzip_exe"
    exec timeout --kill-after=5s 60s env WINEPREFIX="$wine_prefix" "$LOADER" "$sevenzip_exe"
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
TMP_DIR="$(mktemp -d)"
export XDG_RUNTIME_DIR="/tmp/nexus-xdg-runtime-$$"
mkdir -p -m 700 "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
export WINEPREFIX="${WINEPREFIX:-$TMP_DIR/wine-prefix}"
export WINEARCH="${WINEARCH:-win64}"
# Background jobs can inherit SIGINT as ignored. Relay it to FFmpeg so it can
# close MP4 containers cleanly, while making encoding failures non-fatal.
REAL_FFMPEG="$(command -v ffmpeg 2>/dev/null || true)"
if [[ -n "$REAL_FFMPEG" ]]; then
  mkdir -p "$TMP_DIR/ffmpeg-bin"
  cat > "$TMP_DIR/ffmpeg-bin/ffmpeg" <<'FFMPEG_WRAPPER'
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
  chmod +x "$TMP_DIR/ffmpeg-bin/ffmpeg"
  export NEXUS_REAL_FFMPEG="$REAL_FFMPEG"
  export PATH="$TMP_DIR/ffmpeg-bin:$PATH"
fi
ANDROID_HOME="${ANDROID_HOME:-/usr/local/lib/android/sdk}"
BUILD_TOOLS="$ANDROID_HOME/build-tools/35.0.0"
cleanup() {
  local status=$?
  trap - EXIT
  if [[ -n "${ANDROID_EMULATOR_PID:-}" ]]; then
    adb -s "${ANDROID_SERIAL:-emulator-5554}" emu kill >/dev/null 2>&1 || true
    kill "$ANDROID_EMULATOR_PID" >/dev/null 2>&1 || true
    wait "$ANDROID_EMULATOR_PID" 2>/dev/null || true
  fi
  if [[ -n "${WINEPREFIX:-}" ]] && command -v wineserver >/dev/null 2>&1; then
    stop_wineserver "$WINEPREFIX"
  fi
  rm -rf -- "$XDG_RUNTIME_DIR" >/dev/null 2>&1 || true
  rm -rf "$TMP_DIR" || true
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
    env NO_AT_BRIDGE=1 GSK_RENDERER=cairo GDK_BACKEND=x11 LIBGL_ALWAYS_SOFTWARE=1 GTK_USE_PORTAL=0 \
      NEXUS_SMOKE_AUTOCONFIRM=1 NEXUS_RUNTIME_SMOKE="$ROOT/runtime-smoke.sh" \
      python3 "$ROOT/tests/runtime/real-app-evidence.py" "$ecosystem" "$app_id" \
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
export GSK_RENDERER=cairo GDK_BACKEND=x11 LIBGL_ALWAYS_SOFTWARE=1 GTK_USE_PORTAL=0 NO_AT_BRIDGE=1
command -v wine64 >/dev/null || test -x /usr/lib/wine/wine64 || { echo "wine64 is required" >&2; exit 1; }

# Verify the real F-Droid APK when Android SDK tools are available.
# ISO Gate does not need adb, a device, or a full Android emulator.
if [[ -x "$BUILD_TOOLS/apksigner" ]]; then
  APK="$TMP_DIR/privacyfriendly2048.apk"
  echo "[smoke] Download F-Droid 2048 APK" >&2
  timeout --kill-after=2s 100s curl -fL --retry 3 --connect-timeout 15 --max-time 90 \
    https://f-droid.org/repo/org.secuso.privacyfriendly2048_100.apk -o "$APK"
  run_test "Verify F-Droid APK signature" "$BUILD_TOOLS/apksigner" verify --verbose "$APK"
  if [[ -x "$BUILD_TOOLS/aapt2" ]]; then
    echo "[smoke] Verify F-Droid APK package identity" >&2
    badging="$(timeout --kill-after=1s 15s "$BUILD_TOOLS/aapt2" dump badging "$APK")"
    grep -Fq "package: name='org.secuso.privacyfriendly2048'" <<<"$badging"
  fi
  export NEXUS_FDROID_APK="$APK"
else
  echo "[smoke] Android SDK apksigner unavailable; skipping APK package inspection" >&2
fi
# The dedicated runtime-evidence job provisions this AVD. Boot it only when its
# emulator and APK tooling are present; ISO Gate intentionally has neither.
if command -v emulator >/dev/null 2>&1 && command -v adb >/dev/null 2>&1 && \
    [[ -n "${NEXUS_FDROID_APK:-}" ]] && [[ -x "$BUILD_TOOLS/aapt2" ]]; then
  if emulator -list-avds 2>/dev/null | grep -Fxq nexus-evidence; then
    export ANDROID_SERIAL="${ANDROID_SERIAL:-emulator-5554}" NEXUS_ANDROID_TARGET=adb
    echo "[smoke] Boot the CI Android AVD for real F-Droid APK execution" >&2
    timeout --kill-after=5s 180s emulator -avd nexus-evidence -no-window -gpu swiftshader_indirect \
      -no-snapshot -no-audio -no-boot-anim -camera-back none -camera-front none \
      </dev/null >/dev/null 2>&1 &
    ANDROID_EMULATOR_PID=$!
    timeout --kill-after=2s 120s adb -s "$ANDROID_SERIAL" wait-for-device
    boot_deadline=$((SECONDS + 120))
    until [[ "$(adb -s "$ANDROID_SERIAL" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]]; do
      (( SECONDS < boot_deadline )) || { echo "Android AVD did not finish booting" >&2; exit 1; }
      sleep 2
    done
    adb -s "$ANDROID_SERIAL" shell settings put global window_animation_scale 0 >/dev/null
    adb -s "$ANDROID_SERIAL" shell settings put global transition_animation_scale 0 >/dev/null
    run_store_evidence android privacy2048 "2048" "$NEXUS_FDROID_APK"
  else
    echo "[smoke] Android SDK is available but nexus-evidence AVD is absent; skipping APK UI capture" >&2
  fi
else
  echo "[smoke] Android AVD/APK tooling unavailable; retaining signature and manifest checks only" >&2
fi

# Keep a separate Wasmtime smoke check, then exercise the real 2048 PWA through OmniStore.
mkdir -p "$TMP_DIR/webapp"
cp -a "$ROOT/tests/webapp/." "$TMP_DIR/webapp/"
run_test "Build and execute WebAssembly smoke module" bash -c 'python3 "$1/tests/webapp/build_wasm.py" "$2/test.wasm" && test "$("$3" run --invoke advance "$2/test.wasm")" = 1' _ "$ROOT" "$TMP_DIR" "$WASMTIME"
run_test "Compile PE exit smoke" x86_64-w64-mingw32-gcc -Os -static "$ROOT/tests/fixtures/pe-exit-zero.c" -o "$TMP_DIR/pe-exit-zero.exe"
echo "[smoke] Execute PE exit smoke through Wine (max 60s)" >&2
timeout --kill-after=5s 60s xvfb-run -a "$LOADER" "$TMP_DIR/pe-exit-zero.exe"
stop_wineserver "$WINEPREFIX"
timeout --kill-after=2s 300s bash "$ROOT/wine-gui-smoke.sh" "$LOADER" "7zip:auto" "$TMP_DIR/webapp"
if command -v flatpak >/dev/null 2>&1; then
  run_store_evidence linux gnome-mines "Mines"
else
  echo "[smoke] Flatpak unavailable; skipping Flathub GNOME Mines evidence" >&2
fi
