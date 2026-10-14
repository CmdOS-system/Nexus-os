# Nexus OS VM boot testing

The boot smoke test is intentionally non-destructive. It boots the ISO as virtual CD media under QEMU, uses UEFI firmware, attaches no writable system disk, and uses snapshot behavior.

Run:

`bash image/boot-smoke.sh image/work/<candidate>.iso`

Prerequisites: `qemu-system-x86_64`, readable OVMF firmware, GNU `timeout`, and a verified ISO candidate.

## Current automated gate

The guest contains `nexus-boot-ready.service`, enabled for `multi-user.target`. It is ordered after local filesystems and user-session setup, never after `multi-user.target` itself. The helper validates Nexus identity and live-media presence, then emits:

`NEXUS_LIVE_BOOT_READY_V1`

directly to the serial console. The host smoke test fails unless that exact marker is captured.

This proves the Nexus live guest reached the readiness service with the expected OS identity and live-media mount. It does **not** prove graphical login, desktop usability, networking, suspend/resume, installation, or hardware compatibility.

## Required next gates

- verify the graphical session becomes usable;
- verify NetworkManager is active;
- verify clean restart and shutdown;
- repeat UEFI boot;
- test legacy BIOS where supported;
- boot on representative physical hardware;
- only then introduce a writable virtual disk for installer testing.

No physical disk installation should be attempted from this smoke test.
