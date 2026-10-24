#!/usr/bin/env bash
set -euo pipefail
serial="${1:?Android serial required}"
package="${2:?Android package required}"
export SDL_VIDEODRIVER=x11 SDL_AUDIODRIVER=dummy SDL_RENDER_DRIVER=software LIBGL_ALWAYS_SOFTWARE=1
image=/tmp/android-live.png
temporary="/tmp/android-live-chromium.$$.tmp.png"
asset="/tmp/android-apk-chromium.$$.png"
html=/tmp/android-surface.html
cleanup() {
  if [[ -n "${updater:-}" ]]; then kill "$updater" >/dev/null 2>&1 || true; wait "$updater" 2>/dev/null || true; fi
  rm -f "$temporary" "$asset" 2>/dev/null || true
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
chrome="${NEXUS_CHROMIUM_BINARY:-$(command -v chromium || command -v chromium-browser || command -v google-chrome || true)}"
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
<style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#070b14;color:#e7fbff;font:14px sans-serif}
.glass{box-sizing:border-box;width:100%;height:100%;padding:10px;background:linear-gradient(145deg,rgba(27,47,72,.96),rgba(9,16,29,.98));border:2px solid #00d9ef;border-radius:22px;box-shadow:inset 0 0 24px rgba(0,217,239,.18),0 0 20px rgba(0,217,239,.22)}
.bar{height:42px;display:flex;align-items:center;justify-content:space-between;padding:0 18px;color:#e7fbff;letter-spacing:1px}.live{color:#38deed;font-size:11px}
img{display:block;width:100%;height:calc(100% - 48px);object-fit:contain;border-radius:12px}</style></head>
<body><main class="glass"><header class="bar"><span>PRIVACY FRIENDLY 2048</span><span class="live">ANDROID LIVE</span></header><img id="screen" src="file:///tmp/android-live.png"></main><script>
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
done </dev/null >/dev/null 2>&1 &
updater=$!
"$chrome" --user-data-dir="${NEXUS_CHROMIUM_PROFILE:-/tmp/nexus-android-viewer}" \
  --no-sandbox --disable-gpu --disable-dev-shm-usage --no-first-run --no-default-browser-check \
  --allow-file-access-from-files --window-size=780,560 --window-position=710,76 \
  --app="file:///tmp/android-surface.html"
