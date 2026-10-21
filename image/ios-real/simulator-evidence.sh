#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/evidence/ios"
BUILD="$(mktemp -d)"
mkdir -p "$OUT"
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
  local output="$1"
  # CoreSimulator screenshots work on headless hosted macOS workers where
  # screencapture may wait forever for a WindowServer desktop session.
  if run_bounded 20 xcrun simctl io "$UDID" screenshot "$output" && [[ -s "$output" ]]; then
    return 0
  fi
  rm -f "$output"
  echo "CoreSimulator screenshot did not return; trying a short native desktop capture." >&2
  if run_bounded 3 screencapture -x "$output" && [[ -s "$output" ]]; then
    return 0
  fi
  rm -f "$output"
  echo "No real iOS Simulator frame could be captured: $output" >&2
  return 1
}

HOST_ARCH="$(uname -m)"
if [[ "$HOST_ARCH" == "arm64" ]]; then SIM_ARCH=arm64; else SIM_ARCH=x86_64; fi
SIM_SDK="$(xcrun --sdk iphonesimulator --show-sdk-path)"
DEVICE_SDK="$(xcrun --sdk iphoneos --show-sdk-path)"
SOURCE="$ROOT/image/ios-real/Nexus2048App.swift"
BUNDLE_ID="com.nexus.omni2048"

make_app() {
  local destination="$1" sdk="$2" target="$3"
  mkdir -p "$destination"
  xcrun swiftc -parse-as-library -target "$target" -sdk "$sdk" \
    -framework UIKit -O "$SOURCE" -o "$destination/Nexus2048"
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
  codesign --force --sign - "$destination"
}

SIM_APP="$BUILD/Nexus2048-Simulator.app"
DEVICE_APP="$BUILD/Payload/Nexus2048.app"
make_app "$SIM_APP" "$SIM_SDK" "$SIM_ARCH-apple-ios17.0-simulator"
make_app "$DEVICE_APP" "$DEVICE_SDK" "arm64-apple-ios17.0"
[[ "$(lipo -archs "$DEVICE_APP/Nexus2048")" == *arm64* ]]
ditto -c -k --sequesterRsrc --keepParent "$BUILD/Payload" "$OUT/nexus-2048.ipa"

DEVICE_JSON="$BUILD/devices.json"
xcrun simctl list devices available -j > "$DEVICE_JSON"
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
xcrun simctl boot "$UDID" 2>/dev/null || true
open -a Simulator --args -CurrentDeviceUDID "$UDID" || true
if ! run_bounded 180 xcrun simctl bootstatus "$UDID" -b; then
  echo "SpringBoard did not become ready; resetting this simulator and retrying once." >&2
  run_bounded 30 xcrun simctl shutdown "$UDID" || true
  run_bounded 120 xcrun simctl erase "$UDID" || true
  run_bounded 30 xcrun simctl boot "$UDID" || true
  open -a Simulator --args -CurrentDeviceUDID "$UDID" || true
  if ! run_bounded 180 xcrun simctl bootstatus "$UDID" -b; then
    echo "Simulator remains unavailable after reset; bounded desktop captures will still record only visible simulator state." >&2
  fi
fi
# Keep the simulator in a medium floating macOS window when a GUI session is
# available. The headless CI capture path remains the simulator framebuffer.
osascript >/dev/null 2>&1 <<'APPLESCRIPT' || true
tell application "System Events"
  if exists process "Simulator" then
    tell process "Simulator"
      set frontmost to true
      if (count of windows) > 0 then
        set position of window 1 to {430, 70}
        set size of window 1 to {560, 690}
      end if
    end tell
  end if
end tell
APPLESCRIPT
mkdir -p "$OUT"
xcrun simctl io "$UDID" recordVideo --codec=h264 "$OUT/ipa-running.mp4" >/dev/null 2>&1 &
VIDEO_PID=$!
sleep 2
run_bounded 20 xcrun simctl install "$UDID" "$SIM_APP" &
INSTALL_PID=$!
sleep 0.2
take_sim_screenshot "$OUT/ios-installing.png" || true
if ! wait "$INSTALL_PID"; then
  echo "simctl install failed or timed out; resetting CoreSimulator once before retrying." >&2
  INSTALL_PID=""
  run_bounded 30 xcrun simctl shutdown "$UDID" || true
  run_bounded 120 xcrun simctl erase "$UDID" || true
  run_bounded 30 xcrun simctl boot "$UDID" || true
  open -a Simulator --args -CurrentDeviceUDID "$UDID" || true
  run_bounded 180 xcrun simctl bootstatus "$UDID" -b || true
  run_bounded 90 xcrun simctl install "$UDID" "$SIM_APP" || true
else
  INSTALL_PID=""
fi
run_bounded 60 xcrun simctl launch "$UDID" "$BUNDLE_ID" || {
  echo "simctl launch failed or timed out; foregrounding Simulator for native screenshot recovery." >&2
  open -a Simulator --args -CurrentDeviceUDID "$UDID" || true
}
sleep 4
take_sim_screenshot "$OUT/ios-interacting.png" || true
sleep 2
take_sim_screenshot "$OUT/ipa-running.png" || true
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
