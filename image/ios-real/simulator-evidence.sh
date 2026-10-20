#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$ROOT/evidence/ios"
BUILD="$(mktemp -d)"
mkdir -p "$OUT"
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
  xcrun swiftc -target "$target" -sdk "$sdk" -framework UIKit -O "$SOURCE" -o "$destination/Nexus2048"
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
xcrun simctl bootstatus "$UDID" -b
mkdir -p "$OUT"
xcrun simctl io "$UDID" screenshot "$OUT/ios-installing.png"
xcrun simctl io "$UDID" recordVideo --codec=h264 "$OUT/ipa-running.mp4" >/dev/null 2>&1 &
VIDEO_PID=$!
sleep 1
xcrun simctl install "$UDID" "$SIM_APP"
xcrun simctl launch "$UDID" "$BUNDLE_ID"
sleep 5
xcrun simctl io "$UDID" screenshot "$OUT/ios-interacting.png"
cp "$OUT/ios-interacting.png" "$OUT/ipa-running.png"
kill -INT "$VIDEO_PID" 2>/dev/null || true
wait "$VIDEO_PID" 2>/dev/null || true
test -s "$OUT/ipa-running.mp4"
echo "Built an arm64 IPA and captured the running 2048 UIKit app in iOS Simulator."
