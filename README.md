# Nexus OS

Nexus OS is an experimental Linux distribution project focused on usability, reproducible builds, secure updates, and compatibility.

## Current status

Early development. Not certified, production-ready, or validated on physical hardware.

## Engineering milestones

1. Reproducible bootable ISO and signed artifact manifest.
2. QEMU/OVMF UEFI installation and reboot integration tests.
3. Partitioning, rollback, A/B updates, and recovery tests.
4. Desktop shell, accessibility, localization, and graphical installer.
5. Windows app compatibility through isolated Wine/Proton integration.
6. Security hardening, hardware qualification, and release criteria.

## Safety

Test in disposable virtual machines first. Do not install on a primary machine or overwrite disks until independently verified.
