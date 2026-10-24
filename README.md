# Nexus OS

Nexus OS is an experimental Linux distribution project focused on usability, reproducible builds, secure updates, and compatibility.

## Current status

Early development. Not certified, production-ready, or validated on physical hardware.

## Runtime architecture decision (2026-10-18)

Nexus is built on Debian and its real Linux kernel. OmniOS's Rust code is being integrated as the **Nexus OmniSubsystem**, a user-space dispatcher that connects Linux `binfmt_misc` to installed compatibility runtimes. It does not replace the Linux kernel, translate every vendor ABI, or make arbitrary applications universally compatible. The standalone UEFI OmniKernel remains an experimental research target and is not part of Nexus boot.

The current integration and its exact boundaries are documented in [Nexus OmniSubsystem](docs/NEXUS-OMNISUBSYSTEM.md). Windows PE/MSI use Wine, APK routes through Waydroid after validation and user confirmation, Mach-O can use externally installed Darling, WASM uses checksum-verified Wasmtime, CRX opens a separate Chromium extension profile, `.deb` asks before invoking apt, and ELF stays native to Linux. Each runtime has platform and app-specific requirements; actual ISO checks and app acceptance are tracked separately.

## Engineering milestones

1. Reproducible bootable ISO and signed artifact manifest.
2. QEMU/OVMF UEFI installation and reboot integration tests.
3. Partitioning, rollback, A/B updates, and recovery tests.
4. Desktop shell, accessibility, localization, and graphical installer.
5. Windows app compatibility through isolated Wine/Proton integration.
6. Security hardening, hardware qualification, and release criteria.

## Safety

Test in disposable virtual machines first. Do not install on a primary machine or overwrite disks until independently verified.
