#!/usr/bin/env bash
set -euo pipefail
serial="${1:?Android serial required}"
package="${2:?Android package required}"
export SDL_RENDER_DRIVER=software LIBGL_ALWAYS_SOFTWARE=1

focus="$(adb -s "$serial" shell dumpsys window windows 2>/dev/null || true)"
grep -E 'mCurrentFocus|mFocusedApp' <<<"$focus" | grep -Fq "$package" || {
  echo "The real Android package is not in foreground: $package" >&2
  exit 1
}
command -v ffplay >/dev/null || { echo "ffplay is required for native Android screen mirroring" >&2; exit 1; }

set -o pipefail
while :; do
  focus="$(adb -s "$serial" shell dumpsys window windows 2>/dev/null || true)"
  if grep -E 'mCurrentFocus|mFocusedApp' <<<"$focus" | grep -Fq "$package"; then
    adb -s "$serial" exec-out screencap -p || break
  else
    sleep 0.2
  fi
  sleep 0.3
done | ffplay -hide_banner -loglevel error -nostats -an -sn -dn \
  -f image2pipe -framerate 2 -vcodec png -window_title "Privacy Friendly 2048" \
  -x 760 -y 560 -i pipe:0
