#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP="$RUNNER_TEMP/NexusIOSSmoke.app"
OUT="$ROOT/evidence/ios"
mkdir -p "$APP" "$OUT"

[[ "$(uname -m)" == "arm64" ]] || {
  echo "An Apple Silicon macOS runner is required to execute the ARM64 iOS Simulator build." >&2
  exit 1
}

SDK="$(xcrun --sdk iphonesimulator --show-sdk-path)"
xcrun --sdk iphonesimulator swiftc \
  -target arm64-apple-ios17.0-simulator -sdk "$SDK" -parse-as-library \
  -framework UIKit -o "$APP/NexusIOSSmoke" "$ROOT/image/ios-real/NexusIOSSmoke.swift"
file "$APP/NexusIOSSmoke" | grep -Fq 'arm64'

cat > "$APP/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleDevelopmentRegion</key><string>en</string>
  <key>CFBundleExecutable</key><string>NexusIOSSmoke</string>
  <key>CFBundleIdentifier</key><string>com.example.nexus.realios</string>
  <key>CFBundleInfoDictionaryVersion</key><string>6.0</string>
  <key>CFBundleName</key><string>NexusIOSSmoke</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>LSRequiresIPhoneOS</key><true/>
  <key>MinimumOSVersion</key><string>17.0</string>
  <key>UIDeviceFamily</key><array><integer>1</integer></array>
  <key>UIRequiredDeviceCapabilities</key><array><string>arm64</string></array>
  <key>UILaunchScreen</key><dict/>
</dict></plist>
PLIST
plutil -lint "$APP/Info.plist"
codesign --force --deep --sign - "$APP"

device_json="$(xcrun simctl list devices available -j)"
UDID="$(python3 -c 'import json,sys; d=json.load(sys.stdin)["devices"]; print(next(x["udid"] for runtime,items in d.items() if "iOS" in runtime for x in items if x.get("isAvailable") and x["name"].startswith("iPhone")))' <<< "$device_json")"
cleanup() { xcrun simctl shutdown "$UDID" >/dev/null 2>&1 || true; }
trap cleanup EXIT
xcrun simctl boot "$UDID" 2>/dev/null || true
xcrun simctl bootstatus "$UDID" -b
xcrun simctl install "$UDID" "$APP"
xcrun simctl launch "$UDID" com.example.nexus.realios
DATA="$(xcrun simctl get_app_container "$UDID" com.example.nexus.realios data)"
for attempt in $(seq 1 40); do
  if [[ -s "$DATA/Documents/live-frame.txt" ]] && [[ "$(cat "$DATA/Documents/live-frame.txt")" -ge 5 ]]; then break; fi
  sleep 1
done
test "$(cat "$DATA/Documents/live-frame.txt")" -ge 5
xcrun simctl io "$UDID" screenshot "$OUT/ipa-running.png"
test -s "$OUT/ipa-running.png"

mkdir -p "$RUNNER_TEMP/Payload"
cp -R "$APP" "$RUNNER_TEMP/Payload/NexusIOSSmoke.app"
(cd "$RUNNER_TEMP" && /usr/bin/zip -qr "$OUT/nexus-ios-arm64-smoke.ipa" Payload)
echo "ARM64 iOS Simulator app ran live frames $(cat "$DATA/Documents/live-frame.txt"); IPA and simulator screenshot saved."
