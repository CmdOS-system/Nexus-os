#!/usr/bin/env bash
set -euo pipefail
serial="${1:?Android serial required}"
package="${2:?Android package required}"
export SDL_VIDEODRIVER=x11 SDL_AUDIODRIVER=dummy SDL_RENDER_DRIVER=software LIBGL_ALWAYS_SOFTWARE=1
image=/tmp/android-live.png
temporary="/tmp/android-live-chromium.$$.tmp.png"
asset="/tmp/android-apk-chromium.$$.png"
html=/tmp/nexus-fallback-2048.html
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
chrome="$(command -v chromium || command -v chromium-browser || command -v google-chrome || true)"
[[ -n "$chrome" ]] || { echo "A Chromium browser is required for Android screenshot fallback" >&2; exit 1; }
command -v file >/dev/null
rm -f "$image"
frame_ready=0
for attempt in {1..4}; do
  if adb -s "$serial" exec-out screencap -p > "$temporary" 2>/dev/null && valid_png "$temporary"; then
    mv -f "$temporary" "$image"
    frame_ready=1
    break
  fi
  sleep 0.5
done
if [[ "$frame_ready" != "1" ]]; then
  if ! extract_apk_asset; then
    echo "No valid graphics could be extracted from the real Android APK." >&2
    exit 1
  fi
  ffmpeg -v error -y -f lavfi -i "color=c=0x0d1726:s=760x560:d=1" -i "$asset" \
    -filter_complex "[1:v]scale=220:220:force_original_aspect_ratio=decrease[icon];[0:v][icon]overlay=(W-w)/2:(H-h)/2" \
    -frames:v 1 "$image"
  valid_png "$image" || { echo "APK-derived Android frame is not a valid PNG." >&2; exit 1; }
fi
cat > "$html" <<'HTML'
<!doctype html><html><head><meta charset="utf-8"><title>2048</title>
<style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#0d1726}img{width:100%;height:100%;object-fit:contain}</style></head>
<body><img id="screen" src="file:///tmp/android-live.png"><script>
const screen=document.getElementById('screen');setInterval(()=>{screen.src='file:///tmp/android-live.png?frame='+Date.now()},400);
</script></body></html>
HTML
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
"$chrome" --no-sandbox --disable-gpu --disable-dev-shm-usage --no-first-run \
  --allow-file-access-from-files --user-data-dir=/tmp/android-surface-viewer \
  --window-size=780,560 --window-position=710,76 --app="file://$html"
