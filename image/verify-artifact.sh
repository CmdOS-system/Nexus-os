#!/usr/bin/env bash
set -euo pipefail

ARTIFACT_DIR="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/work}"
cd "$ARTIFACT_DIR"

mapfile -t ISOS < <(find . -maxdepth 1 -type f -name '*.iso' -print)
if [ "${#ISOS[@]}" -ne 1 ]; then
  echo "Expected exactly one ISO artifact, found ${#ISOS[@]}" >&2
  exit 1
fi

ISO="${ISOS[0]}"
test -s "$ISO"
test -s SHA256SUMS

sha256sum --check SHA256SUMS

case "$(file -b "$ISO")" in
  *ISO 9660*) ;;
  *)
    echo "Artifact does not look like an ISO 9660 image" >&2
    exit 1
    ;;
esac

echo "Nexus OS ISO artifact checks passed: $ISO"
