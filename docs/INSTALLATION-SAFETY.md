# Nexus OS — Installation safety gate

Status: design specification only. The current Live ISO is **not installable**; `--debian-installer none` is intentional.

## Preconditions before enabling any installer

1. Build and boot the ISO in QEMU using OVMF; preserve guest serial evidence and checksums.
2. Implement a dry-run installer plan that **never writes to disks** and displays target device, stable identifier, size, partitions, encryption, and data-loss warning.
3. Require an explicit, separate user confirmation for destructive operations. No automatic selection of the first disk, no silent partitioning, and no inferred consent.
4. Reject mounted devices, host system devices, symlinks, missing/ambiguous identifiers, and targets that change between planning and execution.
5. Exercise destructive test paths **only** against freshly created disposable QCOW2 images in isolated QEMU guests. Never run partitioning against the GitHub Actions runner host.
6. Validate UEFI boot, persistence across reboots, rollback, filesystem checks, and recovery from interrupted installation.
7. Add a gated CI job and published evidence before changing the live-build `--debian-installer none` setting.

## Current verified scope

The ISO gate verifies image construction, checksum, UEFI Live boot, and readiness markers for the graphical stack and XFCE session. It does **not** verify a disk installation, visual rendering quality, or hardware compatibility.

## Exit criteria

Installer can be enabled only after a disposable-disk end-to-end installation and reboot are repeatably green, with independent review of destructive disk-operation safeguards.
