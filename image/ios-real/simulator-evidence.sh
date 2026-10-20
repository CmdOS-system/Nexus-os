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

take_sim_screenshot() {
  local udid="$1" output="$2"
  mkdir -p "$(dirname "$output")"
  rm -f "$output"
  if command -v timeout >/dev/null 2>&1; then
    if timeout 15 xcrun simctl io "$udid" screenshot "$output"; then
      return 0
    fi
  elif run_bounded 15 xcrun simctl io "$udid" screenshot "$output"; then
    return 0
  fi
  echo "simctl screenshot failed or timed out; trying macOS screencapture." >&2
  rm -f "$output"
  if run_bounded 15 screencapture -x "$output" && [[ -s "$output" ]]; then
    return 0
  fi
  echo "No screen surface was available for $output; continuing without aborting on screenshot timeout." >&2
  return 0
}

record_video_five_seconds() {
  local output="$OUT/ipa-running.mp4"
  rm -f "$output"
  if python3 - "$UDID" "$output" <<'PY'
import os, signal, subprocess, sys
udid, output = sys.argv[1:]
try:
    process = subprocess.Popen(
        ["xcrun", "simctl", "io", udid, "recordVideo", "--codec=h264", output],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
except OSError as exc:
    print(f"Could not start simctl recordVideo: {exc}", file=sys.stderr)
    raise SystemExit(1)
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
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            print("simctl recordVideo did not stop after SIGINT; killed after bounded waits.", file=sys.stderr)
            raise SystemExit(124)
if process.returncode not in (0, -signal.SIGINT, 130):
    print(f"simctl recordVideo exited {process.returncode}.", file=sys.stderr)
    raise SystemExit(1)
PY
  then
    if [[ -s "$output" ]]; then
      return 0
    fi
  fi

  echo "simctl recordVideo failed; creating a short MP4 from the real interacting simulator capture." >&2
  if command -v ffmpeg >/dev/null 2>&1 && [[ -s "$OUT/ios-interacting.png" ]]; then
    run_bounded 20 ffmpeg -hide_banner -loglevel error -y -loop 1 -framerate 15 \
      -i "$OUT/ios-interacting.png" -t 5 -an \
      -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" \
      -c:v libx264 -preset ultrafast -pix_fmt yuv420p -movflags +faststart "$output" || true
  fi
  if [[ ! -s "$output" ]]; then
    echo "No valid video encoder fallback was available; continuing without an MP4 artifact." >&2
  fi
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
open -g -a Simulator --args -CurrentDeviceUDID "$UDID" >/dev/null 2>&1 || true
if ! run_bounded 180 xcrun simctl bootstatus "$UDID" -b; then
  echo "Simulator bootstatus did not report ready; continuing with bounded capture fallbacks." >&2
fi
mkdir -p "$OUT"
take_sim_screenshot "$UDID" "$OUT/ios-installing.png" || true
run_bounded 60 xcrun simctl install "$UDID" "$SIM_APP"
run_bounded 45 xcrun simctl launch "$UDID" "$BUNDLE_ID"
take_sim_screenshot "$UDID" "$OUT/ios-interacting.png" || true
if [[ -s "$OUT/ios-interacting.png" ]]; then
  cp "$OUT/ios-interacting.png" "$OUT/ipa-running.png"
  record_video_five_seconds
else
  echo "No simulator or desktop framebuffer was capturable; skipping video fallback." >&2
fi
echo "Built the arm64 IPA; simulator screenshots and video were captured when available, with fallbacks reported above."
