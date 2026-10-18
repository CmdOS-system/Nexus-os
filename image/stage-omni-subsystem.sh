#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$ROOT/.." && pwd)"
STAGING="$ROOT/staging"
WASMTIME_VERSION="49.0.2"
ASSET="wasmtime-v${WASMTIME_VERSION}-x86_64-linux.tar.xz"
RELEASE_API="https://api.github.com/repos/bytecodealliance/wasmtime/releases/tags/v${WASMTIME_VERSION}"

for tool in cargo curl jq sha256sum tar install; do
  command -v "$tool" >/dev/null || { echo "Required build tool missing: $tool" >&2; exit 1; }
done

cargo build --manifest-path "$PROJECT_ROOT/omnios/Cargo.toml" --release --target x86_64-unknown-linux-gnu -p omni-loader --bin nexus-omniloader
mkdir -p "$STAGING/usr/bin"
install -m 0755 "$PROJECT_ROOT/omnios/target/x86_64-unknown-linux-gnu/release/nexus-omniloader" "$STAGING/usr/bin/nexus-omniloader"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
curl --fail --location --retry 3 --output "$tmp/$ASSET" "https://github.com/bytecodealliance/wasmtime/releases/download/v${WASMTIME_VERSION}/${ASSET}"
digest="$(curl --fail --silent --show-error "$RELEASE_API" | jq -er --arg name "$ASSET" '.assets[] | select(.name == $name) | .digest | select(startswith("sha256:")) | sub("^sha256:"; "")')"
[[ "$digest" =~ ^[0-9a-f]{64}$ ]] || { echo "Invalid Wasmtime release digest from official GitHub API" >&2; exit 1; }
printf '%s  %s\n' "$digest" "$tmp/$ASSET" | sha256sum --check --status || { echo "Wasmtime archive checksum mismatch" >&2; exit 1; }
mkdir "$tmp/extract"
tar -xJf "$tmp/$ASSET" -C "$tmp/extract"
wasmtime="$(find "$tmp/extract" -type f -name wasmtime -perm /111 -print -quit)"
test -n "$wasmtime" && "$wasmtime" --version | grep -F "${WASMTIME_VERSION}"
install -m 0755 "$wasmtime" "$STAGING/usr/bin/wasmtime"
mkdir -p "$STAGING/usr/share/doc/wasmtime"
curl --fail --location --retry 3 \
  "https://raw.githubusercontent.com/bytecodealliance/wasmtime/v${WASMTIME_VERSION}/LICENSE" \
  --output "$STAGING/usr/share/doc/wasmtime/LICENSE"
printf 'Staged nexus-omniloader and verified Wasmtime %s in %s\n' "$WASMTIME_VERSION" "$STAGING"
