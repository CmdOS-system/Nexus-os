#!/usr/bin/env bash
# Run under a disposable D-Bus session and Xvfb, never the user's desktop.
set -euo pipefail
source_xml=${1:?Expected shortcut XML path}
expected=${2:-present}
session_root=$(mktemp -d)
export XDG_CONFIG_HOME="$session_root/config"
export XDG_CACHE_HOME="$session_root/cache"
mkdir -p "$XDG_CONFIG_HOME/xfce4/xfconf/xfce-perchannel-xml" "$XDG_CACHE_HOME"
cp "$source_xml" "$XDG_CONFIG_HOME/xfce4/xfconf/xfce-perchannel-xml/xfce4-keyboard-shortcuts.xml"
xfsettingsd --no-daemon > "$session_root/settings.log" 2>&1 &
settings_pid=$!
trap 'kill "$settings_pid" 2>/dev/null || true; wait "$settings_pid" 2>/dev/null || true; rm -rf "$session_root"' EXIT
for attempt in $(seq 1 30); do
  if [ "$(xfconf-query -c xfce4-keyboard-shortcuts -p /commands/custom/override 2>/dev/null || true)" = true ]; then
    break
  fi
  sleep 1
done
test "$(xfconf-query -c xfce4-keyboard-shortcuts -p /commands/custom/override)" = true
actual=$(xfconf-query -c xfce4-keyboard-shortcuts -p '/commands/custom/<Super>space' 2>/dev/null || true)
if [ "$expected" = missing ]; then
  test "$actual" != /usr/local/bin/nexus-horizon || { echo "Original regression did not reproduce: $actual"; exit 1; }
else
  test "$actual" = /usr/local/bin/nexus-horizon || {
    cat "$session_root/settings.log"
    xfconf-query -c xfce4-keyboard-shortcuts -lv
    echo "Horizon shortcut was not retained: $actual"
    exit 1
  }
fi
# Distribution shortcuts must survive alongside Nexus's default.
test -n "$(xfconf-query -c xfce4-keyboard-shortcuts -p '/commands/custom/<Alt>F2')"
echo "XFCE first-session shortcut check passed ($expected)"
