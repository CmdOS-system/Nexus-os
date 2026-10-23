#!/usr/bin/env bash
set -euo pipefail
serial="${1:?Android serial required}"
package="${2:?Android package required}"
export SDL_VIDEODRIVER=x11 SDL_RENDER_DRIVER=software LIBGL_ALWAYS_SOFTWARE=1

focus="$(adb -s "$serial" shell dumpsys window windows 2>/dev/null || true)"
grep -E 'mCurrentFocus|mFocusedApp' <<<"$focus" | grep -Fq "$package" || {
  echo "The real Android package is not in foreground: $package" >&2
  exit 1
}
command -v ffplay >/dev/null || { echo "ffplay is required for native Android screen mirroring" >&2; exit 1; }

image=/tmp/android-live.png
temporary="/tmp/android-live.$$.tmp.png"
cleanup() {
  if [[ -n "${updater:-}" ]]; then kill "$updater" >/dev/null 2>&1 || true; wait "$updater" 2>/dev/null || true; fi
  rm -f "$temporary"
}
trap cleanup EXIT INT TERM
adb -s "$serial" exec-out screencap -p > "$temporary"
test -s "$temporary"
mv -f "$temporary" "$image"

while :; do
  focus="$(adb -s "$serial" shell dumpsys window windows 2>/dev/null || true)"
  if grep -E 'mCurrentFocus|mFocusedApp' <<<"$focus" | grep -Fq "$package"; then
    if adb -s "$serial" exec-out screencap -p > "$temporary" && test -s "$temporary"; then
      mv -f "$temporary" "$image"
    fi
  fi
  sleep 0.5
done &
updater=$!

ffplay -nostats -loglevel error -window_title "Privacy Friendly 2048" \
  -x 760 -y 560 -loop 0 "$image"
