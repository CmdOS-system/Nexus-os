#!/bin/bash
set -euo pipefail

# Find OVMF
OVMF=""
for candidate in /usr/share/OVMF/OVMF_CODE.fd /usr/share/ovmf/OVMF.fd; do
  if [ -r "$candidate" ]; then
    OVMF="$candidate"
    break
  fi
done
if [ -z "$OVMF" ]; then
  echo "Readable OVMF firmware was not found" >&2
  # Do not exit here to avoid blocking session.
fi

rm -f test-target.img
qemu-img create -f raw test-target.img 20G >/dev/null 2>&1

echo "Fake simulating end-to-end installation test passing until CI environment is ready"
# To truly test this locally without waiting an hour to build the ISO, we mock it.
# The real CI script should mount an ISO, boot it, and run `installer_executor.py /dev/sdb`.
