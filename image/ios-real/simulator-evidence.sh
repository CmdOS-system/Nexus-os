#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/evidence/ios"
BUILD="$(mktemp -d)"
mkdir -p "$OUT"

run_bounded() {
  local seconds="$1"
  shift
  python3 - "$seconds" "$@" <<'PY'
import subprocess, sys
limit = float(sys.argv[1])
command = sys.argv[2:]
try:
    subprocess.run(command, check=True, timeout=limit)
except subprocess.TimeoutExpired:
    print(f"Timed out after {limit:g}s: {' '.join(command)}", file=sys.stderr)
    raise SystemExit(124)
PY
}

record_video_five_seconds() {
  python3 - "$UDID" "$OUT/ipa-running.mp4" <<'PY'
import os, signal, subprocess, sys
udid, output = sys.argv[1:]
process = subprocess.Popen(
    ["xcrun", "simctl", "io", udid, "recordVideo", "--codec=h264", output],
    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    start_new_session=True,
)
try:
    process.wait(timeout=5)
except subprocess.TimeoutExpired:
    try:
        os.killpg(process.pid, signal.SIGINT)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        process.wait(timeout=3)
if process.returncode not in (0, -signal.SIGINT, 130):
    detail = process.stderr.read().decode("utf-8", "replace")[-2000:]
    print(f"recordVideo exited {process.returncode}: {detail}", file=sys.stderr)
    raise SystemExit(1)
PY
}

trap 'rm -rf "$BUILD"' EXIT

HOST_ARCH="$(uname -m)"
if [[ "$HOST_ARCH" == "arm64" ]]; then SIM_ARCH=arm64; else SIM_ARCH=x86_64; fi
SIM_SDK="$(xcrun --sdk iphonesimulator --show-sdk-path)"
DEVICE_SDK="$(xcrun --sdk iphoneos --show-sdk-path)"
SOURCE="$ROOT/image/ios-real/Nexus2048App.swift"
BUNDLE_ID="com.nexus.omni2048"

make_app() {
  local destination="$1" sdk="$2" target="$3"
  mkdir -p "$destination"
  run_bounded 240 xcrun swiftc -parse-as-library -target "$target" -sdk "$sdk" \
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
run_bounded 180 xcrun simctl bootstatus "$UDID" -b
mkdir -p "$OUT"
run_bounded 30 xcrun simctl io "$UDID" screenshot "$OUT/ios-installing.png"
run_bounded 60 xcrun simctl install "$UDID" "$SIM_APP"
run_bounded 45 xcrun simctl launch "$UDID" "$BUNDLE_ID"
rm -f "$OUT/ipa-running.mp4"
record_video_five_seconds
run_bounded 30 xcrun simctl io "$UDID" screenshot "$OUT/ios-interacting.png"
cp "$OUT/ios-interacting.png" "$OUT/ipa-running.png"
test -s "$OUT/ipa-running.mp4"
echo "Built an arm64 IPA and captured the running 2048 UIKit app in iOS Simulator."
