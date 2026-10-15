# Nexus Recovery — architecture and safety gates (draft v0.1)

Status: **design only**. No partitioning, bootloader mutation, OTA installation, or rollback automation is implemented by this document.

## Motivation and source review

ChromiumOS uses separate active and inactive system slots, retains a known-good root filesystem while updating the inactive slot, and confirms a successful boot before treating a new slot as stable. Its firmware/GPT priority and try counters are **ChromiumOS-specific** and must not be assumed to work with generic Debian GRUB or arbitrary UEFI firmware.

Primary upstream design references:
- https://www.chromium.org/chromium-os/chromiumos-design-docs/filesystem-autoupdate/
- https://www.chromium.org/chromium-os/chromiumos-design-docs/boot-design/
- https://chromium.googlesource.com/chromiumos/platform2/+/HEAD/update_engine
- https://www.chromium.org/chromium-os/chromiumos-design-docs/verified-boot/

## Nexus OS constraints

1. Debian Trixie base; preserve APT, security updates, and package provenance.
2. The current **live ISO** and its GRUB configuration are not an installed A/B system. Do not alter the proven live-ISO boot path while designing recovery.
3. Never repartition, format, rewrite EFI NVRAM, or replace an existing bootloader without an explicit user-approved installation flow and a tested backup/restore path.
4. Separate user data from system slots. Encryption and filesystem choices must be designed before installation; never assume /home can be moved without migration.
5. Keep the last known-good slot immutable during candidate deployment; verify downloaded payload signatures and hashes before writing anything.
6. Rollback is not a substitute for data backup. Account for forward-only database migrations and configuration compatibility.
7. Live autologin is **not** an installed-system default. Installed users must retain normal authentication.

## Candidate installed-system model (not implemented)

- ESP: existing EFI boot entry management with explicit restore strategy.
- System A: last-known-good root image.
- System B: inactive candidate root image.
- State: user data, durable application data, update journal, and signed slot metadata.
- Recovery: independently bootable, offline recovery medium and documented manual restore.

Slot metadata must record: generation, build ID, cryptographic digest, candidate/healthy/failed state, boot attempts, prior-good slot, and monotonic transaction ID. Write metadata atomically with fsync and a redundant validated copy; do not trust a single mutable file after power loss.

## Proposed update state machine

IDLE -> FETCHED -> VERIFIED -> STAGED -> PENDING_BOOT -> BOOTING_CANDIDATE -> HEALTHY

Failure branches:
- Fetch/signature/hash failure: ABORT without touching the active system.
- Staging or power-loss failure: retain active slot and resume/restart safely.
- Boot timeout, kernel failure, or failed readiness: revert to previous-good slot after a bounded number of attempts.
- State migration incompatibility: block deployment unless reversible or explicitly backed up.

Only an **installed-system** health agent may mark a slot HEALTHY, after verifying kernel/root identity, essential services, and an actual user-facing graphical session where applicable. A live-ISO serial marker alone is not sufficient proof of installed-system health.

## Release gates

G0: Document threat model, licensing, target hardware, storage budgets and rollback limits.
G1: Pure state-machine model tests (no root privileges or block devices), including malformed metadata.
G2: QEMU with disposable virtual disks: initial install, update, reboot, successful confirmation.
G3: QEMU fault injection: power cut at each transition, corrupted payload, wrong signature, exhausted boot attempts, full disk.
G4: EFI/GRUB recovery validation with both UEFI and legacy BIOS where supported; confirm user data remains intact.
G5: Secure Boot and dm-verity feasibility evaluation; avoid claiming Verified Boot before a real measured and verified chain is demonstrated.
G6: Installer integration, consent screens, real hardware matrix, offline recovery, and repeatable independent audit.

## Implementation sequence

1. Implement an unprivileged Python state-machine simulator and tests.
2. Prototype disk layout exclusively on disposable QEMU images.
3. Evaluate Debian-compatible approaches (e.g. RAUC, systemd-sysupdate, OSTree) against signed updates, GRUB integration, APT compatibility, and recovery guarantees; select only after experiments.
4. Add installed-system update service behind an explicit feature gate; never enable on the current live image by default.
5. Add visual UX only after automated rollback and recovery tests pass.

## Explicit non-goals

- Copying ChromiumOS firmware/GPT bits into generic PCs.
- Shipping ChromeOS proprietary components or branding.
- Executing remote update scripts as root without signature verification.
- Claiming certification or production readiness from a successful VM smoke test.
