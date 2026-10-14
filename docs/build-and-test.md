# Nexus OS build and verification procedure

Status: source-level prototype. No ISO has been built or boot tested.

## Prerequisites
Use a disposable Debian 13 (trixie) amd64 VM with sufficient disk and memory. Install live-build, xorriso, and squashfs-tools.

## Build
Run `bash image/validate.sh` to check basic shell syntax and package manifest. Then run `sudo bash image/build.sh` on a disposable builder. Find output in `image/work/`. Verify SHA256SUMS before distributing.

## VM validation
Boot the resulting ISO in QEMU with UEFI firmware (OVMF). Confirm desktop login, network, shutdown and restart. Repeat on BIOS firmware if supported. Collect screenshots, boot logs and package manifest. Do not install to physical disks: installer is explicitly disabled.

## Release gates
No production release until reproducible build, automated boot tests, installer tests, disk safety, update and rollback, security review, driver coverage, license review and documented hardware compatibility have passed.

## AI integration
Provider adapters and Nexus Agent are design-only at this stage. Never place API keys in source or CI logs.
