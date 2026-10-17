#!/usr/bin/env bash
# Disposable CI desktop. Never attach this script to a user's active session.
set -euo pipefail
test -n "${DISPLAY:-}"
test -n "${DBUS_SESSION_BUS_ADDRESS:-}"
session_root=$(mktemp -d)
export XDG_CONFIG_HOME="$session_root/config"
export XDG_CACHE_HOME="$session_root/cache"
mkdir -p "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" native-desktop-evidence
cp -a image/includes/etc/skel/.config/. "$XDG_CONFIG_HOME/"
dbus-update-activation-environment XDG_CONFIG_HOME XDG_CACHE_HOME
xfce4-session > native-desktop-evidence/session.log 2>&1 &
session_pid=$!
trap 'kill "$session_pid" 2>/dev/null || true; wait "$session_pid" 2>/dev/null || true; rm -rf "$session_root"' EXIT
for attempt in $(seq 1 60); do
  if xfconf-query -c xfce4-desktop -l 2>/dev/null | grep -q '/last-image$'; then break; fi
  sleep 1
done
/bin/sh image/includes/usr/local/libexec/nexus-horizon-appearance
test "$(xfconf-query -c xsettings -p /Net/ThemeName)" = Arc-Dark
test "$(xfconf-query -c xsettings -p /Net/IconThemeName)" = Papirus-Dark
test "$(xfconf-query -c xsettings -p /Gtk/FontName)" = 'Inter 11'
xfconf-query -c xfce4-desktop -lv > native-desktop-evidence/backdrop.txt
xfconf-query -c xsettings -lv > native-desktop-evidence/appearance.txt
grep -q /usr/share/backgrounds/nexus/horizon-aurora.svg native-desktop-evidence/backdrop.txt
# A subsequent login must preserve a user's new wallpaper selection.
property=$(xfconf-query -c xfce4-desktop -l | sed -n '\|^/backdrop/.*/workspace[0-9][0-9]*/last-image$|p' | head -1)
test -n "$property"
xfconf-query -c xfce4-desktop -p "$property" -s /tmp/user-selected-wallpaper.svg
/bin/sh image/includes/usr/local/libexec/nexus-horizon-appearance
test "$(xfconf-query -c xfce4-desktop -p "$property")" = /tmp/user-selected-wallpaper.svg
# Restore the test wallpaper before capturing the native session.
xfconf-query -c xfce4-desktop -p "$property" -s /usr/share/backgrounds/nexus/horizon-aurora.svg
sleep 3
/usr/bin/python3 agent/tests/native_desktop_screenshot.py
echo 'Native XFCE appearance, preference preservation and screenshot passed (not an ISO boot)'
