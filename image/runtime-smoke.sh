#!/usr/bin/env bash
set -euo pipefail

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

# Open Wine's real Notepad GUI on the Nexus XFCE desktop and capture it.
bash "$ROOT/wine-gui-smoke.sh" "$LOADER" "$TEMP/fixtures/minimal.apk" "$TEMP/fixtures/unsigned-extension.crx" "$TEMP/fixtures/wasi-exit-zero.wasm"

# Exercise the macOS and PWA wrappers without claiming either platform app runs.
mkdir "$TEMP/fake-bin"
cat > "$TEMP/fake-bin/darling" <<'SH'
#!/bin/sh
printf '%s\n' "$@" > "$NEXUS_CAPTURE"
SH
cat > "$TEMP/fake-bin/chromium" <<'SH'
#!/bin/sh
printf '%s\n' "$@" > "$NEXUS_CAPTURE"
SH
chmod 0755 "$TEMP/fake-bin/darling" "$TEMP/fake-bin/chromium"
export NEXUS_CAPTURE="$TEMP/macho-args"
printf '\317\372\355\376NEXUS' > "$TEMP/probe.macho"
PATH="$TEMP/fake-bin:$PATH" "$LOADER" "$TEMP/probe.macho" 'argument with spaces'
grep -Fxq shell "$NEXUS_CAPTURE"
grep -Fq '/Volumes/SystemRoot' "$NEXUS_CAPTURE"
grep -Fq "argument with spaces" "$NEXUS_CAPTURE"
echo "Mach-O dispatch and Darling path/argument bridge passed with a test double; no macOS binary was executed."

export NEXUS_CAPTURE="$TEMP/chromium-args"
PATH="$TEMP/fake-bin:$PATH" "$LOADER" --webapp https://example.org/nexus
grep -Fxq -- '--app=https://example.org/nexus' "$NEXUS_CAPTURE"
echo "PWA launcher passed --app URL to Chromium; browser runtime was represented by a test double."
