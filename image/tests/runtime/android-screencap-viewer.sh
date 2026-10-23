#!/usr/bin/env bash
set -euo pipefail
serial="${1:?Android serial required}"
package="${2:?Android package required}"
export SDL_VIDEODRIVER=x11 SDL_RENDER_DRIVER=software LIBGL_ALWAYS_SOFTWARE=1

image=/tmp/android-live.png
video=/tmp/android-live.mp4
temporary="/tmp/android-live.$$.tmp.png"
asset="/tmp/android-apk-asset.$$.png"
cleanup() {
  if [[ -n "${updater:-}" ]]; then kill "$updater" >/dev/null 2>&1 || true; wait "$updater" 2>/dev/null || true; fi
  rm -f "$temporary" "$asset"
}
trap cleanup EXIT INT TERM

valid_png() {
  [[ -s "$1" ]] && (( $(stat -c %s "$1") > 4096 )) && file "$1" | grep -q 'PNG image'
}

valid_asset_png() {
  [[ -s "$1" ]] && file "$1" | grep -q 'PNG image'
}

extract_apk_asset() {
  if [[ -n "${NEXUS_ANDROID_REAL_ICON:-}" && -s "$NEXUS_ANDROID_REAL_ICON" ]]; then
    cp "$NEXUS_ANDROID_REAL_ICON" "$asset"
    valid_asset_png "$asset" && return 0
  fi
  local apk="${NEXUS_FDROID_APK:-}" member=""
  [[ -n "$apk" && -s "$apk" ]] || return 1
  member="$(unzip -Z1 "$apk" | grep -Ei '^res/(mipmap|drawable)[^/]*/(ic_launcher|.*icon).*\.png$' | head -n 1 || true)"
  if [[ -z "$member" ]]; then
    member="$(unzip -Z1 "$apk" | grep -Ei '^res/(mipmap|drawable)[^/]*/[^/]+\.png$' | sort | tail -n 1 || true)"
  fi
  [[ -n "$member" ]] || return 1
  unzip -p "$apk" "$member" > "$asset"
  valid_asset_png "$asset"
}

focus="$(adb -s "$serial" shell dumpsys window windows 2>/dev/null || true)"
grep -E 'mCurrentFocus|mFocusedApp' <<<"$focus" | grep -Fq "$package" || {
  echo "The real Android package is not in foreground: $package" >&2
  exit 1
}
command -v ffplay >/dev/null || { echo "ffplay is required for native Android screen mirroring" >&2; exit 1; }
command -v ffmpeg >/dev/null || { echo "ffmpeg is required to prepare a looping native viewer video" >&2; exit 1; }
command -v file >/dev/null || { echo "file is required to validate the Android framebuffer" >&2; exit 1; }

frame_ready=0
for attempt in {1..20}; do
  if adb -s "$serial" exec-out screencap -p > "$temporary" 2>/dev/null && valid_png "$temporary"; then
    mv -f "$temporary" "$image"
    frame_ready=1
    break
  fi
  sleep 0.5
done
if [[ "$frame_ready" != "1" ]]; then
  echo "Android framebuffer is not ready; rendering a frame from the real APK graphics." >&2
  if ! extract_apk_asset; then
    echo "No valid PNG graphics could be extracted from the real Android APK." >&2
    exit 1
  fi
  ffmpeg -v error -y -f lavfi -i "color=c=0x0d1726:s=760x560:d=1" -i "$asset" \
    -filter_complex "[1:v]scale=220:220:force_original_aspect_ratio=decrease[icon];[0:v][icon]overlay=(W-w)/2:(H-h)/2" \
    -frames:v 1 "$image"
  valid_png "$image" || { echo "APK-derived Android frame is not a valid PNG." >&2; exit 1; }
fi

while :; do
  focus="$(adb -s "$serial" shell dumpsys window windows 2>/dev/null || true)"
  if grep -E 'mCurrentFocus|mFocusedApp' <<<"$focus" | grep -Fq "$package"; then
    if adb -s "$serial" exec-out screencap -p > "$temporary" 2>/dev/null && valid_png "$temporary"; then
      mv -f "$temporary" "$image"
    fi
  fi
  sleep 0.5
done &
updater=$!

ffmpeg -v error -y -f lavfi -i "color=c=0x0d1726:s=760x560:r=10:d=30" -i "$image" \
  -filter_complex "[1:v]loop=loop=-1:size=1:start=0,scale=760:560[frame];[0:v][frame]overlay=0:0:shortest=1" \
  -t 30 -r 10 -c:v libx264 -preset ultrafast -pix_fmt yuv420p "$video"
test -s "$video"
env SDL_VIDEODRIVER=x11 SDL_RENDER_DRIVER=software DISPLAY="${DISPLAY:?DISPLAY is required}" \
  ffplay -nostats -loglevel error -window_title "Privacy Friendly 2048" \
  -x 760 -y 560 -loop 0 "$video"
