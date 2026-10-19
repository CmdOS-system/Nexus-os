#!/usr/bin/env bash
set -euo pipefail

# Keep one session bus alive for every graphical smoke test and evidence capture.
if [[ "${NEXUS_RUNTIME_SESSION:-0}" != "1" && -z "${DBUS_SESSION_BUS_ADDRESS:-}" ]]; then
  command -v dbus-run-session >/dev/null || {
    echo "dbus-run-session is required for graphical runtime smoke tests" >&2
    exit 1
  }
  exec dbus-run-session -- env NEXUS_RUNTIME_SESSION=1 "$BASH" "$0" "$@"
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$ROOT/.." && pwd)"
LOADER="$ROOT/staging/usr/bin/nexus-omniloader"
WASMTIME="$ROOT/staging/usr/bin/wasmtime"
TEMP="$(mktemp -d)"
cleanup() {
  local status=$?
  trap - EXIT
  if [[ -n "${WINEPREFIX:-}" ]] && command -v wineserver >/dev/null 2>&1; then
    WINEPREFIX="$WINEPREFIX" wineserver -k >/dev/null 2>&1 || true
    timeout 15s env WINEPREFIX="$WINEPREFIX" wineserver -w >/dev/null 2>&1 || true
  fi
  if ! rm -rf -- "$TEMP"; then
    chmod -R u+rwX -- "$TEMP" 2>/dev/null || true
    rm -rf -- "$TEMP" || status=$?
  fi
  exit "$status"
}
trap cleanup EXIT

for tool in python3 unzip x86_64-w64-mingw32-gcc xvfb-run; do
  command -v "$tool" >/dev/null || { echo "Required runtime smoke tool missing: $tool" >&2; exit 1; }
done
test -x "$LOADER"
test -x "$WASMTIME"
test -s "$ROOT/staging/usr/lib/nexus/nexus-omniloader-ui.py"
test -s "$ROOT/staging/usr/lib/nexus/nexus-system-sound.py"
export NEXUS_SUBSYSTEM_HELPER="$ROOT/staging/usr/lib/nexus"
export NEXUS_SOUND_DISABLED=1
command -v wine64 >/dev/null || test -x /usr/lib/wine/wine64 || {
  echo "wine64 is required for the real PE execution smoke test" >&2; exit 1;
}

python3 "$PROJECT_ROOT/omnios/loader/tests/make_fixtures.py" "$TEMP/fixtures"

apk_result="$("$LOADER" --inspect-apk "$TEMP/fixtures/minimal.apk")"
grep -Fq 'package=com.example.nexus.smoke' <<< "$apk_result"
grep -Fq 'classes.dex=valid' <<< "$apk_result"
echo "APK AXML package and DEX header inspection passed. (Structural fixture; not installed.)"

if ! crx_result="$("$LOADER" --inspect-crx "$TEMP/fixtures/unsigned-extension.crx" 2>&1)"; then
  printf 'CRX inspection failed:\\n%s\\n' "$crx_result" >&2
  exit 1
fi
grep -Fq 'CRX v3' <<< "$crx_result"
grep -Fq 'manifest.json' <<< "$crx_result"
echo "CRX envelope and extension manifest inspection passed. (Unsigned fixture; never installed.)"

ipa_result="$("$LOADER" --inspect-ipa "$TEMP/fixtures/minimal.ipa")"
grep -Fq 'com.example.nexus.iossmoke' <<< "$ipa_result"
grep -Fq 'Mach-O ARM64 móvil=true' <<< "$ipa_result"
echo "IPA ZIP integrity, Payload app bundle, Info.plist metadata and mobile ARM64 Mach-O inspection passed. (Structural fixture; not executed.)"

"$WASMTIME" run "$TEMP/fixtures/wasi-exit-zero.wasm"
echo "WASI command executed with Wasmtime and exited 0."

# Verify the Linux dispatcher actually launches a PE executable in Wine.
x86_64-w64-mingw32-gcc -Os -static "$ROOT/tests/fixtures/pe-exit-zero.c" -o "$TEMP/pe-exit-zero.exe"
file "$TEMP/pe-exit-zero.exe" | grep -Fq 'PE32+ executable'
export WINEARCH=win64
export WINEPREFIX="$TEMP/wine-prefix"
export WINEDEBUG=-all
xvfb-run -a "$LOADER" "$TEMP/pe-exit-zero.exe"
echo "x86_64 PE executable ran through nexus-omniloader and Wine with exit 0."

# Build a real Win32 GUI PE and a WebAssembly-backed PWA for the graphical smoke.
x86_64-w64-mingw32-gcc -Os -municode -mwindows \
  "$ROOT/tests/fixtures/pe-dynamic-gui.c" -o "$TEMP/nexus-live-win32.exe"
file "$TEMP/nexus-live-win32.exe" | grep -Fq 'PE32+ executable'
mkdir -p "$TEMP/webapp"
cp -a "$ROOT/tests/webapp/." "$TEMP/webapp/"
python3 "$ROOT/tests/webapp/build_wasm.py" "$TEMP/webapp/app.wasm"
"$WASMTIME" validate "$TEMP/webapp/app.wasm"

# Android and iOS evidence is produced by the dedicated device/simulator jobs.
bash "$ROOT/wine-gui-smoke.sh" "$LOADER" "$TEMP/nexus-live-win32.exe" "$TEMP/webapp"
