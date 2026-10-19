#!/usr/bin/env bash
set -euo pipefail

# Keep a single D-Bus session for the Xvfb apps and screenshots.
if [[ "${NEXUS_RUNTIME_SESSION:-0}" != "1" && -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]]; then
  command -v dbus-run-session >/dev/null || { echo "dbus-run-session is required" >&2; exit 1; }
  exec dbus-run-session -- env NEXUS_RUNTIME_SESSION=1 "$BASH" "$0" "$@"
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$ROOT/.." && pwd)"
LOADER="$ROOT/staging/usr/bin/nexus-omniloader"
WASMTIME="$ROOT/staging/usr/bin/wasmtime"
TEMP="$(mktemp -d)"
LD64_LLD="$(command -v ld64.lld || find /usr/bin -maxdepth 1 -name 'ld64.lld-*' -executable -print | sort -V | tail -n 1)"
APK_NATIVE_PAYLOAD="$ROOT/android-real/app/src/main/jniLibs/arm64-v8a/libnexus_apk_payload.so"
export WINEPREFIX="${WINEPREFIX:-$TEMP/wine-prefix}"
export WINEARCH="${WINEARCH:-win64}"
ANDROID_HOME="${ANDROID_HOME:-/usr/local/lib/android/sdk}"
ANDROID_JAR="$ANDROID_HOME/platforms/android-35/android.jar"
BUILD_TOOLS="$ANDROID_HOME/build-tools/35.0.0"
cleanup() {
  local status=$?
  trap - EXIT
  if [[ -n "${WINEPREFIX:-}" ]] && command -v wineserver >/dev/null 2>&1; then
    WINEPREFIX="$WINEPREFIX" wineserver -k >/dev/null 2>&1 || true
  fi
  rm -f "$APK_NATIVE_PAYLOAD" 2>/dev/null || true
  rm -rf -- "$TEMP" || status=$?
  exit "$status"
}
trap cleanup EXIT

run_test() {
  local label="$1"; shift
  echo "[smoke] $label" >&2
  timeout --kill-after=1s 15s "$@"
}
run_fast() {
  local label="$1"; shift
  echo "[smoke] $label (max 25s)" >&2
  timeout --kill-after=1s 25s "$@"
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
  timeout --kill-after=1s 15s xvfb-run -a -s '-screen 0 1280x720x24 -nolisten tcp' \
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
  for attempt in $(seq 1 20); do
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
    finish_recorder "$recorder_pid"
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
  -f x11grab -video_size 1280x720 -framerate 15 -i "$DISPLAY" -t 10 -an \
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
  fi
}
for tool in python3 unzip zip clang x86_64-w64-mingw32-gcc aarch64-linux-gnu-gcc qemu-aarch64-static xvfb-run javac java node xfwm4; do
  command -v "$tool" >/dev/null || { echo "Required runtime smoke tool missing: $tool" >&2; exit 1; }
done
test -n "$LD64_LLD" || { echo "ld64.lld is required to produce the ARM64 Mach-O" >&2; exit 1; }
for tool in "$BUILD_TOOLS/aapt2" "$BUILD_TOOLS/d8" "$BUILD_TOOLS/zipalign"; do
  test -x "$tool" || { echo "Android SDK tool missing: $tool" >&2; exit 1; }
done
test -s "$ANDROID_JAR" || { echo "Android SDK android.jar is missing: $ANDROID_JAR" >&2; exit 1; }
test -x "$LOADER" && test -x "$WASMTIME"
export NEXUS_SUBSYSTEM_HELPER="$ROOT/staging/usr/lib/nexus"
export NEXUS_SOUND_DISABLED=1
command -v wine64 >/dev/null || test -x /usr/lib/wine/wine64 || { echo "wine64 is required" >&2; exit 1; }

# Compile the app Java sources to JVM classes and DEX, plus the ARM64 payload, under one 25s ceiling.
mkdir -p "$TEMP/classes" "$TEMP/dex"
run_fast "Compile APK DEX and ARM64 payload" bash -c '
  set -euo pipefail
  javac -J-XX:TieredStopAtLevel=1 --release 8 -classpath "$1" -d "$3/classes" \
    "$2/android-real/app/src/main/java/com/example/nexus/realapp/MainActivity.java" \
    "$2/android-real/app/src/main/java/com/example/nexus/realapp/PayloadLogic.java"
  mapfile -d "" class_files < <(find "$3/classes" -name "*.class" -print0)
  JAVA_TOOL_OPTIONS=-XX:TieredStopAtLevel=1 "$4/d8" --lib "$1" --min-api 23 --output "$3/dex" "${class_files[@]}"
  aarch64-linux-gnu-gcc -O2 -static "$2/android-real/native/nexus-payload.c" -o "$3/libnexus_apk_payload.so"
' _ "$ANDROID_JAR" "$ROOT" "$TEMP" "$BUILD_TOOLS"
run_test "Execute APK Java bytecode logic in JVM" bash -c 'java -cp "$1/classes" com.example.nexus.realapp.PayloadLogic | tee "$1/jvm-output.txt"' _ "$TEMP"
run_test "Verify APK payload ELF architecture" bash -c 'file "$1" | grep -Fq "ARM aarch64"' _ "$TEMP/libnexus_apk_payload.so"
mkdir -p "$(dirname "$APK_NATIVE_PAYLOAD")"
cp "$TEMP/libnexus_apk_payload.so" "$APK_NATIVE_PAYLOAD"

# Assemble a valid APK directly with aapt2, D8 output, and zipalign; with no external build system or dependency resolution.
APK="$TEMP/nexus-runtime.apk"
run_test "Link APK manifest with aapt2" "$BUILD_TOOLS/aapt2" link -o "$TEMP/resources.apk" \
  --manifest "$ROOT/android-real/app/src/main/AndroidManifest.xml" -I "$ANDROID_JAR" \
  --min-sdk-version 23 --target-sdk-version 28
mkdir -p "$TEMP/apk/lib/arm64-v8a"
run_test "Assemble APK bytecode and native payload" bash -c '
  unzip -q "$1/resources.apk" -d "$1/apk"
  cp "$1/dex/classes.dex" "$1/apk/classes.dex"
  cp "$1/libnexus_apk_payload.so" "$1/apk/lib/arm64-v8a/libnexus_apk_payload.so"
  (cd "$1/apk" && zip -qr "$1/unsigned.apk" .)
' _ "$TEMP"
run_test "Align APK package" "$BUILD_TOOLS/zipalign" -f 4 "$TEMP/unsigned.apk" "$APK"
run_test "Extract and execute APK ARM64 ELF with qemu" bash -c 'unzip -p "$1" lib/arm64-v8a/libnexus_apk_payload.so > "$2/apk-payload" && chmod +x "$2/apk-payload" && qemu-aarch64-static "$2/apk-payload" | tee "$2/apk-output.txt" && grep -Fq "6 x 7 = 42" "$2/apk-output.txt"' _ "$APK" "$TEMP"

run_recorded_test "Capture APK runtime output in GTK and MP4" "$PROJECT_ROOT/evidence/android/apk-running.mp4" env NO_AT_BRIDGE=1 python3 "$ROOT/tests/runtime/evidence-card.py" "Android APK · ARM64 + JVM" "$(cat "$TEMP/apk-output.txt" "$TEMP/jvm-output.txt")" "$PROJECT_ROOT/evidence/android/apk-running.png"

# Compile a freestanding ARM64 function as both an iOS Mach-O and the same raw instruction payload.
mkdir -p "$TEMP/ios/Payload/Nexus.app"
run_test "Compile iOS ARM64 Mach-O payload" clang -target arm64-apple-ios17.0 -c "$ROOT/ios-real/arm64-payload.S" -o "$TEMP/ios/payload.o"
run_test "Link iOS ARM64 Mach-O executable" "$LD64_LLD" -arch arm64 -platform_version ios 17.0 17.0 -e _nexus_ipa_payload "$TEMP/ios/payload.o" -o "$TEMP/ios/Payload/Nexus.app/Nexus"
run_test "Extract ARM64 __text payload from Mach-O" python3 "$ROOT/ios-real/extract-macho-text.py" "$TEMP/ios/Payload/Nexus.app/Nexus" "$TEMP/ios/payload.bin"
run_test "Build static ARM64 payload runner" aarch64-linux-gnu-gcc -O2 -static "$ROOT/ios-real/arm64-runner.c" -o "$TEMP/ios/Payload/Nexus.app/NexusArm64Runner"
cp "$TEMP/ios/payload.bin" "$TEMP/ios/Payload/Nexus.app/PayloadARM64.bin"
run_test "Execute extracted iOS ARM64 instructions under qemu" bash -c 'qemu-aarch64-static "$1" "$2" | tee "$3/ios-output.txt"' _ "$TEMP/ios/Payload/Nexus.app/NexusArm64Runner" "$TEMP/ios/Payload/Nexus.app/PayloadARM64.bin" "$TEMP"
cat > "$TEMP/ios/Payload/Nexus.app/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?><plist version="1.0"><dict><key>CFBundleExecutable</key><string>Nexus</string><key>CFBundleIdentifier</key><string>com.example.nexus.ios</string><key>CFBundleName</key><string>Nexus</string><key>CFBundlePackageType</key><string>APPL</string></dict></plist>
PLIST
mkdir -p "$PROJECT_ROOT/evidence/ios"
run_test "Package IPA bundle" bash -c 'cd "$1/ios" && zip -qr "$2/evidence/ios/nexus-arm64-runtime.ipa" Payload' _ "$TEMP" "$PROJECT_ROOT"
run_recorded_test "Capture IPA runtime output in GTK and MP4" "$PROJECT_ROOT/evidence/ios/ipa-running.mp4" env NO_AT_BRIDGE=1 python3 "$ROOT/tests/runtime/evidence-card.py" "iOS IPA · extracted ARM64 __text" "$(cat "$TEMP/ios-output.txt")" "$PROJECT_ROOT/evidence/ios/ipa-running.png"

# Validate real Wasm execution and build the live PWA used by the Chromium GUI capture.
mkdir -p "$TEMP/webapp"
cp -a "$ROOT/tests/webapp/." "$TEMP/webapp/"
run_test "Build WebAssembly module" python3 "$ROOT/tests/webapp/build_wasm.py" "$TEMP/webapp/app.wasm"
wasm_counter="$(run_test "Execute Wasm module" "$WASMTIME" run --invoke advance "$TEMP/webapp/app.wasm")"
test "$wasm_counter" = "1"
run_test "Compile PE exit smoke" x86_64-w64-mingw32-gcc -Os -static "$ROOT/tests/fixtures/pe-exit-zero.c" -o "$TEMP/pe-exit-zero.exe"
run_test "Execute PE exit smoke through Wine" bash -c 'xvfb-run -a "$1" "$2"' _ "$LOADER" "$TEMP/pe-exit-zero.exe"
WINEPREFIX="$WINEPREFIX" wineserver -k >/dev/null 2>&1 || true
run_test "Compile real Win32 GUI PE" x86_64-w64-mingw32-gcc -Os -municode -mwindows "$ROOT/tests/fixtures/pe-dynamic-gui.c" -o "$TEMP/nexus-live-win32.exe"
run_test "Capture live Win32 and PWA GUI" bash "$ROOT/wine-gui-smoke.sh" "$LOADER" "$TEMP/nexus-live-win32.exe" "$TEMP/webapp"
