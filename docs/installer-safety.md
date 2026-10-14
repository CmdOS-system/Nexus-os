# Nexus OS installer safety gates

Nexus OS must not enable disk installation until destructive-path testing is complete.

## Required gates

1. Live ISO boots successfully in UEFI and legacy BIOS virtual machines.
2. Installer detects target disks without modifying them during discovery.
3. Every destructive partitioning operation requires an explicit confirmation screen showing the exact target disk.
4. Installation tests cover empty disks, existing Linux, existing Windows, UEFI/GPT and failure/interruption cases.
5. Bootloader installation and recovery are verified.
6. Encryption behavior is documented and recovery material is handled safely.
7. Installation cannot silently erase an unselected disk.
8. Automated VM snapshots are used for repeatable destructive tests.
9. Hardware installation remains blocked until VM gates pass.

The current image intentionally uses `--debian-installer none`. This is a safety feature, not a missing release toggle.

## Update and rollback gate

Before stable release, Nexus OS also needs an update mechanism with integrity verification and a tested recovery/rollback path. An update that leaves the system unbootable must be recoverable without reinstalling the OS.
