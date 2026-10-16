# Nexus OS — Installer architecture (proposal)

## Scope and trust boundaries

The shipped Debian Trixie Live ISO remains non-installable. This proposal describes a future installer with a **read-only planning stage** and a separately authorized executor. Planning must never call partitioning or formatting tools.

## Phase 1: inventory and dry-run

- Discover candidate devices via `lsblk --json --bytes --output NAME,PATH,TYPE,SIZE,MODEL,SERIAL,TRAN,MOUNTPOINTS,RO,RM,PKNAME` and resolve stable /dev/disk/by-id identities where available.
- Treat discovery output as untrusted. Reject missing or duplicate stable identifiers, mounted partitions, read-only devices, loop devices, and the currently booted system disk.
- Display target path, serial, capacity, existing partition table, proposed EFI System Partition and Linux filesystem, encryption choice, and irreversible data-loss warning.
- Serialize a plan with a device fingerprint (stable ID, size, topology, partition-table identifier) and expiration; never accept a model-generated path as execution authority.

## Phase 2: explicit authorization

- User must review the plan and confirm destruction of the **specific** target. Authorization is single-use and bound to the immutable plan fingerprint.
- Re-enumerate immediately before execution. Abort on any change, ambiguity, mounted filesystem, or unexpected device.
- Run executor with least privilege; audit commands and exit codes. No automatic fallback to another disk.

## Phase 3: isolated integration tests

- Create fresh disposable QCOW2 targets with `qemu-img create -f qcow2`.
- Boot Nexus ISO via QEMU/OVMF with only the test target attached. Never pass through host block devices.
- Exercise partitioning, UEFI bootloader installation, first boot, persistence, interrupted-install recovery and rollback; archive guest logs and checksums.
- Keep CI installer tests in a separate workflow/job from the non-destructive ISO build gate.

## Release gates

The installer is **blocked** until dry-run tests, destructive QCOW2-only end-to-end tests, UEFI reboot, persistence, error handling, and security review all pass. Do not change `--debian-installer none` before those gates are met.

## Documentation references

- Debian live-build manual: https://live-team.pages.debian.net/live-manual/html/live-manual/index.en.html
- util-linux lsblk: https://man7.org/linux/man-pages/man8/lsblk.8.html
- QEMU disk images: https://www.qemu.org/docs/master/tools/qemu-img.html
