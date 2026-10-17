#!/usr/bin/env bash
# Disposable developer laboratory, not the end-user installer.
set -euo pipefail
mkdir -p windows-evidence
work=$(mktemp -d)
export WINEPREFIX="$work/prefix" WINEARCH=win64
export WINEDLLOVERRIDES="mscoree,mshtml=" WINEDEBUG=-all
trap 'wineserver -k 2>/dev/null || true; rm -rf "$work"' EXIT
wine --version > windows-evidence/runtime.txt
dpkg-query -W wine wine64 libwine >> windows-evidence/runtime.txt
url=https://github.com/ip7z/7zip/releases/download/26.04/7z2604-x64.exe
curl --fail --location --retry 2 --max-time 120 "$url" -o "$work/setup.exe"
echo "d54bf805f9f3704d1e8db2fa3498ae7ef2df0312b40b558e7c71c734430a665d  $work/setup.exe" | sha256sum -c - > windows-evidence/installer-checksum.txt
timeout 120s wineboot -u > windows-evidence/wineboot.log 2>&1
timeout 120s wine "$work/setup.exe" /S > windows-evidence/install.log 2>&1
exe="$WINEPREFIX/drive_c/Program Files/7-Zip/7z.exe"
gui="$WINEPREFIX/drive_c/Program Files/7-Zip/7zFM.exe"
test -f "$exe"
test -f "$gui"
printf 'Nexus Windows compatibility: contenido de prueba.\n' > "$work/nexus sample.txt"
input_win=$(winepath -w "$work/nexus sample.txt" | tr -d '\r')
archive_win=$(winepath -w "$work/result.zip" | tr -d '\r')
timeout 60s wine "$exe" a -tzip "$archive_win" "$input_win" > windows-evidence/archive-create.log 2>&1
python3 - "$work/result.zip" <<'PYZIP'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as archive:
    assert archive.testzip() is None
    assert archive.read('nexus sample.txt') == 'Nexus Windows compatibility: contenido de prueba.\n'.encode()
print('Windows 7-Zip produced a valid ZIP with exact expected content')
PYZIP
wineserver -k
timeout 60s wine "$exe" t "$archive_win" > windows-evidence/archive-reopen.log 2>&1
wine "$gui" > windows-evidence/gui.log 2>&1 &
sleep 10
xwininfo -root -tree > windows-evidence/windows.txt
grep -q '7-Zip' windows-evidence/windows.txt
python3 - <<'PYIMAGE'
import os
from PIL import ImageGrab
ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save('windows-evidence/7zip-windows-gui.png')
PYIMAGE
printf '%s\n' '7-Zip 26.04 x64: installer, archive content, Wine restart and GUI window passed. Debian laboratory, not Nexus ISO or disk reboot.' > windows-evidence/result.txt
