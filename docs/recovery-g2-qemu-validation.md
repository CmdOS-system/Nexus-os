# Recovery G2: virtual-machine validation plan

**Status:** design only. No successful UEFI/QEMU boot is claimed.

## References

- Boot Loader Specification: https://uapi-group.org/specifications/specs/boot_loader_specification/
- systemd automatic boot assessment: https://www.freedesktop.org/software/systemd/man/latest/systemd-boot.html
- QEMU system emulation: https://www.qemu.org/docs/master/system/
- OVMF / edk2: https://github.com/tianocore/tianocore.github.io/wiki/OVMF

## Lab requirements

Use a disposable virtual disk and OVMF firmware with a separate writable VARS
copy. Never point QEMU at the host's EFI System Partition or physical disks.
Check availability of `qemu-system-x86_64`, `qemu-img`, `bootctl`,
`systemd-bless-boot`, and OVMF firmware before attempting an end-to-end test.

## Test matrix

| ID | Fault | Expected observation |
| --- | --- | --- |
| VM-01 | Known-good slot A | Boots and remains selectable |
| VM-02 | Stage verified slot B | Boot counter decreases before kernel transfer |
| VM-03 | B fails repeatedly | B becomes exhausted and A is selected |
| VM-04 | B reports trusted health | B is blessed and remains selected |
| VM-05 | Power loss during metadata update | Previous valid metadata is recovered |
| VM-06 | EFI entry or kernel missing | Fail closed to A or recovery shell |
| VM-07 | Untrusted B image | Rejected before any EFI entry is activated |
| VM-08 | Two update workers | No duplicate generation or lost boot attempts |

## Architectural constraint

The Python Recovery G2 store and systemd-boot each maintain retry state.
A production implementation must define one authoritative retry mechanism,
otherwise a double decrement or inconsistent rollback may occur. Prefer
systemd-boot's boot counting for UEFI attempts and use the Python store only
for verified image inventory / transaction journaling after integration tests
prove that this division is safe.

## Acceptance gate

Do not label Nexus OS installable until boot images, EFI configuration,
signature verification, persistent user-data isolation, rollback, and
crash-injection tests have all passed on a disposable VM, then on a separate
non-primary test machine.
