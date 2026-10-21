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

find_7zip_gui() {
  local prefix="$1" candidate
  for candidate in \
    "$prefix/drive_c/Program Files/7-Zip/7zFM.exe" \
    "$prefix/drive_c/Program Files (x86)/7-Zip/7zFM.exe" \
    "$prefix/drive_c/Program Files/7-Zip/7zG.exe" \
    "$prefix/drive_c/Program Files (x86)/7-Zip/7zG.exe"; do
    if [[ -s "$candidate" ]]; then printf '%s\n' "$candidate"; return 0; fi
  done
  find "$prefix" -type f \( -iname '7zFM.exe' -o -iname '7zG.exe' \) -print -quit 2>/dev/null || true
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
      sevenzip_exe="$(find_7zip_gui "$wine_prefix")"
      if [[ -z "$sevenzip_exe" ]]; then
        curl -fL --retry 2 --connect-timeout 10 --max-time 60 \
          https://github.com/ip7z/7zip/releases/download/26.04/7z2604-x64.exe -o "$installer"
        timeout --kill-after=5s 60s env WINEPREFIX="$wine_prefix" "$LOADER" "$installer" /S || \
          echo "The silent 7-Zip installer did not finish cleanly; searching the prefix and trying archive extraction." >&2
        stop_wineserver "$wine_prefix"
      fi
      sevenzip_exe="$(find_7zip_gui "$wine_prefix")"
      # The OmniLoader dispatch is the primary installer path. Some Wine
      # prefixes report a successful dispatch before the NSIS child has
      # finished creating its GUI files, so complete the same official
      # installer through Wine if its executable is still absent.
      if [[ -z "$sevenzip_exe" || ! -s "$sevenzip_exe" ]]; then
        wine_bin="$(command -v wine 2>/dev/null || command -v wine64 2>/dev/null || true)"
        if [[ -n "$wine_bin" && -s "$installer" ]]; then
          timeout --kill-after=5s 90s env WINEPREFIX="$wine_prefix" "$wine_bin" "$installer" /S || true
          stop_wineserver "$wine_prefix"
          sevenzip_exe="$(find_7zip_gui "$wine_prefix")"
        fi
      fi
      if [[ -z "$sevenzip_exe" || ! -s "$sevenzip_exe" ]]; then
        extract_dir="$wine_prefix/drive_c/Program Files/7-Zip"
        mkdir -p "$extract_dir"
        extractor="$(command -v 7z 2>/dev/null || command -v 7zz 2>/dev/null || command -v 7za 2>/dev/null || true)"
        if [[ -n "$extractor" ]]; then
          timeout --kill-after=2s 30s "$extractor" x "$installer" "-o$extract_dir" -y \
            >/dev/null 2>&1 || true
        fi
        sevenzip_exe="$(find_7zip_gui "$wine_prefix")"
      fi
      test -n "$sevenzip_exe" && test -s "$sevenzip_exe"
      echo "7-Zip 26.04 installed from the official signed Windows installer."
      exit 0
    fi
    wine_prefix="${WINEPREFIX:-$HOME/.local/share/nexus/wine/omnistore}"
    stop_wineserver "$wine_prefix"
    sevenzip_exe="$(find_7zip_gui "$wine_prefix")"
    test -n "$sevenzip_exe" && test -s "$sevenzip_exe"
    exec timeout --kill-after=5s 60s env WINEPREFIX="$wine_prefix" "$LOADER" "$sevenzip_exe" \\
      "Z:\\tmp"
  fi
  if [[ "$target" == flatpak:* ]]; then
    app_id="${target#flatpak:}"
    if [[ "$action" == "--store-install" ]]; then exec "$LOADER" --install-flatpak "$app_id"; fi
    exec "$LOADER" --run-flatpak "$app_id"
  fi
  if [[ "$ecosystem" == "android" ]]; then
    [[ -f "$target" ]] || { echo "Android package does not exist: $target" >&2; exit 2; }
    [[ -n "${ANDROID_SERIAL:-}" ]] || { echo "Android install/open requires an active ADB device." >&2; exit 2; }
    # Force Nexus OmniLoader's Android route through the active Android user
    # space. Its APK path installs the package and requests the launch activity
    # with ADB; this is the real app, not a rendered package preview.
    export NEXUS_ANDROID_TARGET=adb
    exec timeout --kill-after=5s 180s "$LOADER" "$target"
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
# Use one explicit AVD directory for both avdmanager and emulator. CI tools can
# otherwise write the AVD under ANDROID_USER_HOME while emulator searches a
# different default when the workflow changes HOME/XDG context.
export ANDROID_USER_HOME="${ANDROID_USER_HOME:-$HOME/.android}"
export ANDROID_AVD_HOME="${ANDROID_AVD_HOME:-$ANDROID_USER_HOME/avd}"
mkdir -p "$ANDROID_AVD_HOME"
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
  local ecosystem="$1" evidence_ecosystem="$1" app_id="$2" title="$3" package="${4:-}" video primary
  case "$ecosystem" in
    windows) video="wine-gui-running.mp4"; primary="wine-gui-running.png" ;;
    android) video="apk-running.mp4"; primary="apk-running.png" ;;
    ios) video="ipa-running.mp4"; primary="ipa-running.png" ;;
    web) video="crx-pwa-running.mp4"; primary="crx-pwa-running.png" ;;
    linux) video="linux-app-running.mp4"; primary="linux-app-running.png" ;;
    *) echo "Unknown evidence ecosystem: $ecosystem" >&2; return 2 ;;
  esac
  run_recorded_test "Nexus OmniStore $ecosystem install/open evidence" \
    "$PROJECT_ROOT/evidence/$evidence_ecosystem/$video" \
    env NO_AT_BRIDGE=1 GSK_RENDERER=cairo GDK_BACKEND=x11 LIBGL_ALWAYS_SOFTWARE=1 GTK_USE_PORTAL=0 \
      NEXUS_SMOKE_AUTOCONFIRM=1 NEXUS_RUNTIME_SMOKE="$ROOT/runtime-smoke.sh" \
      python3 "$ROOT/tests/runtime/real-app-evidence.py" "$ecosystem" "$app_id" \
      "$PROJECT_ROOT/evidence/$evidence_ecosystem/$evidence_ecosystem-installing.png" \
      "$PROJECT_ROOT/evidence/$evidence_ecosystem/$evidence_ecosystem-interacting.png" "$title" "$package"
  cp "$PROJECT_ROOT/evidence/$evidence_ecosystem/$evidence_ecosystem-interacting.png" \
    "$PROJECT_ROOT/evidence/$evidence_ecosystem/$primary"
}
# wmctrl is intentionally optional; the evidence helper falls back to xwininfo/xdotool.
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
    icon_member="$(sed -n "s/^application-icon-[^:]*:'\\([^']*\\)'.*/\\1/p" <<<"$badging" | head -n 1)"
    if [[ "$icon_member" != *.png ]]; then icon_member=""; fi
    if [[ -z "$icon_member" ]]; then
      icon_member="$(unzip -Z1 "$APK" | grep -Ei '^res/(mipmap|drawable)[^/]*/(ic_launcher|.*icon).*\\.png$' | sort | tail -n 1 || true)"
    fi
    if [[ -z "$icon_member" ]]; then
      icon_member="$(unzip -Z1 "$APK" | grep -Ei '^res/(mipmap|drawable)[^/]*/[^/]+\\.png$' | sort | tail -n 1 || true)"
    fi
    package_label="$(sed -n "s/^application-label:'\\(.*\\)'$/\\1/p" <<<"$badging" | head -n 1)"
    launch_activity="$(sed -n "s/^launchable-activity: name='\\([^']*\\)'.*/\\1/p" <<<"$badging" | head -n 1)"
    export NEXUS_ANDROID_PACKAGE_NAME="org.secuso.privacyfriendly2048"
    export NEXUS_ANDROID_PACKAGE_LABEL="${package_label:-F-Droid 2048}"
    if [[ -n "$launch_activity" ]]; then export NEXUS_ANDROID_LAUNCH_ACTIVITY="$launch_activity"; fi
    if [[ -n "$icon_member" ]]; then
      APK_ICON="$TMP_DIR/fdroid-2048-icon.png"
      unzip -p "$APK" "$icon_member" > "$APK_ICON"
      python3 - "$APK_ICON" <<'PY'
from pathlib import Path
import sys
if Path(sys.argv[1]).read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
    raise SystemExit("F-Droid APK icon resource is not a PNG")
PY
      export NEXUS_ANDROID_REAL_ICON="$APK_ICON"
    elif [[ "${NEXUS_REQUIRE_REAL_EVIDENCE:-0}" == "1" ]]; then
      echo "The real F-Droid APK did not expose a PNG launcher icon." >&2
      exit 1
    fi
  fi
  export NEXUS_FDROID_APK="$APK"
else
  echo "[smoke] Android SDK apksigner unavailable; skipping APK package inspection" >&2
fi
# The runtime-evidence job installs the emulator and system image, but do not
# require an AVD to have been pre-created. Create one from the installed image
# when needed so this path remains usable on fresh GitHub-hosted runners.
if command -v emulator >/dev/null 2>&1 && command -v adb >/dev/null 2>&1 && \
    [[ -n "${NEXUS_FDROID_APK:-}" ]] && [[ -x "$BUILD_TOOLS/aapt2" ]]; then
  AVD_NAME="${NEXUS_AVD_NAME:-nexus-evidence}"
  avd_exists() {
    local config="$ANDROID_AVD_HOME/$AVD_NAME.avd/config.ini"
    [[ -s "$config" ]] && grep -q '^image\.sysdir\.1=' "$config" && return 0
    emulator -list-avds 2>/dev/null | grep -Fxq "$AVD_NAME"
  }
  if ! avd_exists; then
    AVDMANAGER="$(command -v avdmanager 2>/dev/null || true)"
    if [[ -z "$AVDMANAGER" ]]; then
      AVDMANAGER="$(find "$ANDROID_HOME/cmdline-tools" -type f -name avdmanager -perm /111 -print -quit 2>/dev/null || true)"
    fi
    SYSTEM_IMAGE="system-images;android-35;default;x86_64"
    IMAGE_DIR="$ANDROID_HOME/system-images/android-35/default/x86_64"
    if [[ -x "$AVDMANAGER" && -d "$IMAGE_DIR" ]]; then
      echo "[smoke] Create an Android AVD on demand from the installed SDK image" >&2
      rm -rf "$ANDROID_AVD_HOME/$AVD_NAME.avd" "$ANDROID_AVD_HOME/$AVD_NAME.ini"
      if ! printf 'no\n' | timeout --kill-after=2s 90s "$AVDMANAGER" create avd --force \
          -n "$AVD_NAME" -k "$SYSTEM_IMAGE" --device pixel_2 \
          -p "$ANDROID_AVD_HOME/$AVD_NAME.avd"; then
        echo "Android AVD creation failed; avdmanager output above is required to diagnose the installed SDK image/profile." >&2
      fi
      if ! avd_exists; then
        echo "avdmanager returned without a valid $AVD_NAME AVD in ANDROID_AVD_HOME=$ANDROID_AVD_HOME." >&2
      fi
    else
      echo "Real Android UI evidence requires avdmanager and the Android 35 x86_64 system image." >&2
    fi
  fi
  AVD_CONFIG="$ANDROID_AVD_HOME/$AVD_NAME.avd/config.ini"
  if [[ -s "$AVD_CONFIG" ]]; then
    set_avd_property() {
      local key="$1" value="$2"
      if grep -q "^${key}=" "$AVD_CONFIG"; then
        sed -i "s|^${key}=.*|${key}=${value}|" "$AVD_CONFIG"
      else
        printf '%s=%s\n' "$key" "$value" >> "$AVD_CONFIG"
      fi
    }
    set_avd_property hw.lcd.width 720
    set_avd_property hw.lcd.height 1280
    set_avd_property hw.lcd.density 240
    set_avd_property hw.ramSize 2048
    set_avd_property hw.cpu.ncore 2
  fi
  ANDROID_RUNTIME_READY=0
  if avd_exists; then
    export ANDROID_SERIAL="${ANDROID_SERIAL:-emulator-5554}" NEXUS_ANDROID_TARGET=adb
    ACCEL_ARGS=()
    ACCEL_CHECK="$(timeout --kill-after=1s 10s emulator -accel-check 2>&1 || true)"
    if ! grep -Eqi 'installed and usable|is usable' <<<"$ACCEL_CHECK"; then
      echo "[smoke] KVM acceleration unavailable; using the emulator's software CPU mode" >&2
      ACCEL_ARGS=(-accel off)
    fi
    boot_android_avd() {
      local mode="$1" boot_limit="$2" boot_deadline
      shift 2
      echo "[smoke] Boot Android AVD in $mode mode for real F-Droid APK execution (limit ${boot_limit}s)" >&2
      local emulator_log="$TMP_DIR/android-emulator-${mode// /-}.log"
      : > "$emulator_log"
      timeout --kill-after=5s "${boot_limit}s" emulator -avd "$AVD_NAME" -port 5554 -memory 2048 -cores 2 \
        -no-window -gpu swiftshader \
        -no-snapshot -no-audio -no-boot-anim -camera-back none -camera-front none "$@" \
        </dev/null >>"$emulator_log" 2>&1 &
      ANDROID_EMULATOR_PID=$!
      timeout --kill-after=1s 15s adb start-server >/dev/null 2>&1 || true
      if ! timeout --kill-after=2s 180s adb -s "$ANDROID_SERIAL" wait-for-device; then
        tail -n 40 "$emulator_log" >&2 || true
        return 1
      fi
      boot_deadline=$((SECONDS + boot_limit - 20))
      until [[ "$(timeout --kill-after=1s 8s adb -s "$ANDROID_SERIAL" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" == "1" ]]; do
        if (( SECONDS >= boot_deadline )); then
          tail -n 40 "$emulator_log" >&2 || true
          return 1
        fi
        sleep 2
      done
      return 0
    }
    if [[ ${#ACCEL_ARGS[@]} -eq 0 ]]; then
      if boot_android_avd "KVM accelerated" 420; then
        ANDROID_RUNTIME_READY=1
      fi
    fi
    if [[ "$ANDROID_RUNTIME_READY" != "1" ]]; then
      if [[ ${#ACCEL_ARGS[@]} -eq 0 ]]; then
        echo "[smoke] KVM boot failed; restarting once with software CPU and a clean AVD" >&2
        adb -s "$ANDROID_SERIAL" emu kill >/dev/null 2>&1 || true
        kill "$ANDROID_EMULATOR_PID" >/dev/null 2>&1 || true
        wait "$ANDROID_EMULATOR_PID" 2>/dev/null || true
        ANDROID_EMULATOR_PID=""
        timeout --kill-after=1s 10s adb kill-server >/dev/null 2>&1 || true
        timeout --kill-after=1s 15s adb start-server >/dev/null 2>&1 || true
        timeout --kill-after=2s 20s adb -s "$ANDROID_SERIAL" wait-for-disconnect >/dev/null 2>&1 || true
      fi
      if boot_android_avd "software fallback" 900 -accel off -wipe-data; then
        ANDROID_RUNTIME_READY=1
      else
        if [[ "${NEXUS_REQUIRE_REAL_EVIDENCE:-0}" == "1" ]]; then
          echo "Android software AVD did not boot; refusing to replace real APK execution with a package preview." >&2
          exit 1
        fi
        echo "Android software AVD did not boot; skipping Android UI evidence (APK metadata/signature checks remain separate)." >&2
      fi
    fi
    if [[ "$ANDROID_RUNTIME_READY" == "1" ]]; then
      timeout --kill-after=1s 15s adb -s "$ANDROID_SERIAL" shell settings put global window_animation_scale 0 >/dev/null 2>&1 || true
      timeout --kill-after=1s 15s adb -s "$ANDROID_SERIAL" shell settings put global transition_animation_scale 0 >/dev/null 2>&1 || true
      run_store_evidence android privacy2048 "2048" "$NEXUS_FDROID_APK"
    elif [[ "${NEXUS_REQUIRE_REAL_EVIDENCE:-0}" == "1" ]]; then
      echo "No valid Android AVD is available; refusing to report a package preview as real Android execution." >&2
      exit 1
    fi
  elif [[ "${NEXUS_REQUIRE_REAL_EVIDENCE:-0}" == "1" ]]; then
    echo "Android emulator tooling or a valid AVD is unavailable; real Android app execution cannot be evidenced." >&2
    exit 1
  fi
else
  echo "[smoke] Android AVD/APK tooling unavailable; no Android UI evidence will be fabricated." >&2
  if [[ "${NEXUS_REQUIRE_REAL_EVIDENCE:-0}" == "1" ]]; then
    echo "The real-runtime evidence job requires an active Android AVD and APK tooling." >&2
    exit 1
  fi
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
  if [[ "${NEXUS_REQUIRE_REAL_EVIDENCE:-0}" == "1" ]]; then
    echo "Real Linux app evidence is required, but Flatpak is unavailable." >&2
    exit 1
  fi
fi

if [[ "${NEXUS_REQUIRE_REAL_EVIDENCE:-0}" == "1" ]]; then
  run_test "Validate real ecosystem evidence PNGs and MP4s" \
    python3 "$ROOT/tests/runtime/validate-evidence.py" --evidence-root "$PROJECT_ROOT/evidence" \
      --ecosystems windows web android linux
fi


