# Recovery G2 — A/B boot confirmation contract

Status: design specification; not evidence of hardware validation.

## Goal
An update must never overwrite the currently booted root filesystem. A newly staged slot is tentative until a boot health check explicitly confirms it. After exhausted attempts, boot the previously confirmed slot.

## Invariants
1. Active and confirmed slot must not be written by an update transaction.
2. Verify update authenticity (trusted signature) and image integrity before staging; SHA-256 alone does not authenticate a publisher.
3. Stage only the inactive slot. Flush payload and metadata before making it a boot candidate.
4. Record transaction metadata redundantly with monotonic generation and checksums; reject torn, inconsistent, or invalid records.
5. Set a finite boot-attempt budget (initial proposal: 3); decrement before booting a tentative slot.
6. Mark a tentative slot confirmed only after a successful userspace health check, including required mounts and core services.
7. If attempts are exhausted, or integrity validation fails, select the last confirmed slot.
8. Never mark both slots unbootable automatically. If neither is trustworthy, enter recovery mode without destructive writes.
9. User data must live outside replaceable root slots and must be protected separately; OS rollback is not data rollback.
10. All recovery actions must be auditable without recording secrets.

## Suggested states
CONFIRMED -> STAGING -> STAGED -> PENDING_BOOT -> CONFIRMED
PENDING_BOOT -> RETRY_PENDING -> ROLLBACK -> CONFIRMED_OLD
Any invalid metadata or no usable slot -> RECOVERY_REQUIRED

## Fault injection test matrix
- Power loss while writing inactive payload: old slot remains bootable.
- Power loss between payload flush and boot-selection commit: old slot remains selected or recoverable.
- Power loss during redundant metadata update: choose highest valid generation.
- Tamper inactive payload after staging: reject boot or installation.
- Three failed boot attempts: automatic fallback to last confirmed slot.
- Successful boot without health confirmation: remains tentative.
- Health confirmation after full service readiness: commits new slot.
- Corrupt primary metadata: recover from secondary copy.
- Corrupt both metadata copies: safe recovery, no arbitrary slot selection.
- Attempt update targeting active slot: hard failure.
- Unsupported bundle signature or platform compatibility: reject before writes.
- Disk full, I/O error, interrupted download: no active-slot mutation.

## Implementation sequencing
1. Add a pure deterministic state machine and unit tests.
2. Add disposable file-backed block devices for A/B fault injection.
3. Add durable metadata writes (temporary file, fsync, atomic rename, directory fsync) and crash replay tests.
4. Connect bootloader retry counters and userspace health confirmation.
5. Exercise QEMU/OVMF cold boot, failed boot, rollback, and persistence.
6. Gate releases on signed image verification, CI evidence, and hardware tests.

## References
- https://github.com/systemd/systemd/blob/main/docs/AUTOMATIC_BOOT_ASSESSMENT.md
- https://github.com/systemd/systemd/blob/main/man/systemd-sysupdate.xml
- https://github.com/rauc/rauc/blob/master/docs/basic.rst
- https://github.com/rauc/rauc/blob/master/docs/reference.rst
- https://www.qemu.org/docs/master/system/replay.html
