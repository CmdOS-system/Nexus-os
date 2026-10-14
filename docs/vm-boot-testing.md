# Nexus OS VM boot testing

The first boot smoke test is intentionally non-destructive. It boots the ISO as virtual CD media under QEMU, uses UEFI firmware, does not attach a writable system disk, and enables QEMU snapshot behavior.

Run:

`bash image/boot-smoke.sh image/work/<candidate>.iso`

Prerequisites include QEMU x86_64, OVMF and the verified ISO candidate.

## What this test proves

At this stage the script only proves that QEMU can start the candidate and that serial boot evidence is produced. It does not yet prove that the graphical desktop became usable.

## Required next checks

A stronger guest-level test must verify:
- kernel/userspace reaches a known Live target;
- graphical session starts;
- NetworkManager is active;
- restart and shutdown complete;
- UEFI boot is repeatable;
- BIOS boot is tested separately where supported.

No physical disk installation should be attempted from this smoke test.
