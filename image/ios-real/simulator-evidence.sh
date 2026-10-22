#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/evidence/ios"
BUILD="$(mktemp -d)"
mkdir -p "$OUT"
rm -f "$OUT/ios-installing.png" "$OUT/ios-interacting.png" "$OUT/ipa-running.png" "$OUT/ipa-running.mp4"
VIDEO_PID=""
INSTALL_PID=""
cleanup() {
  if [[ -n "$INSTALL_PID" ]]; then
    kill -TERM "$INSTALL_PID" 2>/dev/null || true
    wait "$INSTALL_PID" 2>/dev/null || true
  fi
  if [[ -n "$VIDEO_PID" ]]; then
    kill -INT "$VIDEO_PID" 2>/dev/null || true
    for _ in {1..30}; do
      kill -0 "$VIDEO_PID" 2>/dev/null || break
      sleep 0.2
    done
    kill -TERM "$VIDEO_PID" 2>/dev/null || true
    sleep 0.2
    kill -KILL "$VIDEO_PID" 2>/dev/null || true
    wait "$VIDEO_PID" 2>/dev/null || true
  fi
  rm -rf "$BUILD"
}
trap cleanup EXIT

run_bounded() {
  local seconds="$1"; shift
  python3 - "$seconds" "$@" <<'PY'
import os, signal, subprocess, sys
limit = int(sys.argv[1])
command = sys.argv[2:]
process = subprocess.Popen(command, stdin=subprocess.DEVNULL, start_new_session=True)
try:
    status = process.wait(timeout=limit)
except subprocess.TimeoutExpired:
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
    print(f"Timed out after {limit}s: {' '.join(command)}", file=sys.stderr)
    raise SystemExit(124)
raise SystemExit(status)
PY
}

take_sim_screenshot() {
  local output="$1" temporary="${1%.png}.capture.png"
  # Keep this evidence tied to the simulator device framebuffer. A macOS desktop
  # screencapture is not an iOS app frame and must not be substituted for it.
  rm -f "$temporary"
  if run_bounded 20 xcrun simctl io "$UDID" screenshot "$temporary" && [[ -s "$temporary" ]]; then
    mv -f "$temporary" "$output"
    return 0
  fi
  rm -f "$temporary"
  echo "CoreSimulator did not return a device frame: $output" >&2
  return 1
}

capture_installing_frame() {
  local attempt
  for attempt in 1 2 3 4 5; do
    if take_sim_screenshot "$OUT/ios-installing.png"; then
      return 0
    fi
    sleep 2
  done
  return 1
}

# Give CoreSimulatorService time to publish its runtimes on a fresh hosted runner.
# The first query may trigger service startup and take close to a minute.
run_bounded 90 xcrun simctl list runtimes >/dev/null 2>&1 || true

HOST_ARCH="$(uname -m)"
if [[ "$HOST_ARCH" == "arm64" ]]; then SIM_ARCH=arm64; else SIM_ARCH=x86_64; fi
SIM_SDK="$(run_bounded 90 xcrun --sdk iphonesimulator --show-sdk-path)"
DEVICE_SDK="$(run_bounded 90 xcrun --sdk iphoneos --show-sdk-path)"
SOURCE="$ROOT/image/ios-real/Nexus2048App.swift"
BUNDLE_ID="com.nexus.omni2048"

make_app() {
  local destination="$1" sdk="$2" target="$3"
  mkdir -p "$destination"
  run_bounded 240 xcrun swiftc -parse-as-library -target "$target" -sdk "$sdk" \
    -Xcc -isysroot -Xcc "$sdk" -framework UIKit -O "$SOURCE" -o "$destination/Nexus2048"
  cat > "$destination/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleExecutable</key><string>Nexus2048</string>
<key>CFBundleIdentifier</key><string>$BUNDLE_ID</string>
<key>CFBundleName</key><string>Nexus 2048</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleVersion</key><string>1</string>
<key>CFBundleShortVersionString</key><string>1.0</string>
<key>LSRequiresIPhoneOS</key><true/>
<key>MinimumOSVersion</key><string>17.0</string>
<key>UIDeviceFamily</key><array><integer>1</integer><integer>2</integer></array>
<key>UILaunchScreen</key><dict/>
<key>UIRequiredDeviceCapabilities</key><array><string>arm64</string></array>
<key>UISupportedInterfaceOrientations</key><array><string>UIInterfaceOrientationPortrait</string></array>
</dict></plist>
PLIST
  run_bounded 30 codesign --force --sign - "$destination"
}

SIM_APP="$BUILD/Nexus2048-Simulator.app"
DEVICE_APP="$BUILD/Payload/Nexus2048.app"
make_app "$SIM_APP" "$SIM_SDK" "$SIM_ARCH-apple-ios17.0-simulator"
make_app "$DEVICE_APP" "$DEVICE_SDK" "arm64-apple-ios17.0"
[[ "$(lipo -archs "$DEVICE_APP/Nexus2048")" == *arm64* ]]
run_bounded 30 ditto -c -k --sequesterRsrc --keepParent "$BUILD/Payload" "$OUT/nexus-2048.ipa"

DEVICE_JSON="$BUILD/devices.json"
run_bounded 90 xcrun simctl list devices available -j > "$DEVICE_JSON"
UDID="$(python3 - "$DEVICE_JSON" <<'PY'
import json, sys
devices=json.load(open(sys.argv[1], encoding="utf-8"))["devices"]
for runtime in sorted(devices, reverse=True):
    for device in devices[runtime]:
        if device.get("isAvailable") and "iPhone" in device.get("name", ""):
            print(device["udid"]); raise SystemExit(0)
raise SystemExit("No available iPhone Simulator device")
PY
)"
run_bounded 30 xcrun simctl boot "$UDID" 2>/dev/null || true
run_bounded 10 open -g -a Simulator --args -CurrentDeviceUDID "$UDID" || true
if ! run_bounded 180 xcrun simctl bootstatus "$UDID" -b; then
  echo "SpringBoard did not become ready; resetting this simulator and retrying once." >&2
  run_bounded 30 xcrun simctl shutdown "$UDID" || true
  run_bounded 120 xcrun simctl erase "$UDID" || true
  run_bounded 30 xcrun simctl boot "$UDID" || true
  run_bounded 10 open -g -a Simulator --args -CurrentDeviceUDID "$UDID" || true
  if ! run_bounded 180 xcrun simctl bootstatus "$UDID" -b; then
    echo "Simulator remains unavailable after reset; cannot produce genuine iOS app evidence." >&2
    exit 1
  fi
fi
# Wait for CoreSimulator's framebuffer after boot recovery, then capture the
# actual device screen before installation begins. Never substitute the host desktop.
if ! capture_installing_frame; then
  echo "Simulator framebuffer is not ready before installation; retrying after Simulator activation." >&2
  run_bounded 10 open -g -a Simulator --args -CurrentDeviceUDID "$UDID" || true
  sleep 2
  capture_installing_frame || true
fi
# Keep the simulator in a medium floating macOS window when a GUI session is
# available. The headless CI capture path remains the simulator framebuffer.
run_bounded 10 osascript \
  -e 'tell application "System Events"' \
  -e 'if exists process "Simulator" then' \
  -e 'tell process "Simulator"' \
  -e 'set frontmost to true' \
  -e 'if (count of windows) > 0 then' \
  -e 'set position of window 1 to {430, 70}' \
  -e 'set size of window 1 to {560, 690}' \
  -e 'end if' -e 'end tell' -e 'end if' -e 'end tell' \
  >/dev/null 2>&1 || true

mkdir -p "$OUT"
xcrun simctl io "$UDID" recordVideo --codec=h264 "$OUT/ipa-running.mp4" >/dev/null 2>&1 &
VIDEO_PID=$!
sleep 2
capture_installing_frame || true
run_bounded 120 xcrun simctl install "$UDID" "$SIM_APP" &
INSTALL_PID=$!
sleep 0.2
take_sim_screenshot "$OUT/ios-installing.png" || true
if ! wait "$INSTALL_PID"; then
  echo "simctl install failed or timed out; resetting CoreSimulator once before retrying." >&2
  INSTALL_PID=""
  run_bounded 30 xcrun simctl shutdown "$UDID" || true
  run_bounded 120 xcrun simctl erase "$UDID" || true
  run_bounded 30 xcrun simctl boot "$UDID" || true
  run_bounded 10 open -g -a Simulator --args -CurrentDeviceUDID "$UDID" || true
  run_bounded 180 xcrun simctl bootstatus "$UDID" -b
  capture_installing_frame || true
  run_bounded 180 xcrun simctl install "$UDID" "$SIM_APP"
else
  INSTALL_PID=""
fi
if [[ ! -s "$OUT/ios-installing.png" ]]; then
  echo "The simulator did not expose its framebuffer before app launch; retrying a genuine device screenshot after installation." >&2
  capture_installing_frame || {
    echo "CoreSimulator still has no readable device framebuffer; refusing to generate a substitute image." >&2
    exit 1
  }
fi
# A first launch may wait on SpringBoard longer than the command itself needs.
# Bound it to two minutes, but keep the already-booted simulator alive and capture
# its genuine framebuffer if CoreSimulator does not return from the launch RPC.
launch_status=0
run_bounded 120 xcrun simctl launch "$UDID" "$BUNDLE_ID" || launch_status=$?
if (( launch_status != 0 )); then
  if (( launch_status != 124 )); then
    echo "simctl launch failed with status $launch_status." >&2
    exit "$launch_status"
  fi
  echo "simctl launch exceeded 120s; checking the active Simulator framebuffer and continuing with real device captures." >&2
fi
sleep 4
take_sim_screenshot "$OUT/ios-interacting.png"
sleep 2
take_sim_screenshot "$OUT/ipa-running.png"
kill -INT "$VIDEO_PID" 2>/dev/null || true
for _ in {1..30}; do
  kill -0 "$VIDEO_PID" 2>/dev/null || break
  sleep 0.2
done
kill -TERM "$VIDEO_PID" 2>/dev/null || true
sleep 0.2
kill -KILL "$VIDEO_PID" 2>/dev/null || true
wait "$VIDEO_PID" 2>/dev/null || true
for evidence in ios-installing.png ios-interacting.png ipa-running.png ipa-running.mp4; do
  if [[ ! -s "$OUT/$evidence" ]]; then
    echo "Missing iOS runtime evidence before validation: $OUT/$evidence" >&2
    exit 1
  fi
done
# The validator is pure Python and performs no X11/XQuartz probes; simulator PNG
# decoding can take longer than a short smoke-test timeout on macOS runners.
run_bounded 120 python3 "$ROOT/image/tests/runtime/validate-evidence.py" --evidence-root "$ROOT/evidence" --ecosystems ios
echo "Built the arm64 IPA; captured and validated distinct real Simulator frames and its runtime video."
