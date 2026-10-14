# Nexus OS release gates

A version is not installable/stable merely because an ISO file can be produced.

## Gate A — source
- shell/source validation;
- dependency manifest review;
- no embedded credentials;
- build documentation.

## Gate B — live image
- ISO builds from a clean builder;
- checksum generated;
- UEFI boot;
- BIOS boot where supported;
- desktop, network, restart and shutdown verified.

## Gate C — installer
- destructive VM test matrix passes;
- target disk confirmation;
- bootloader/recovery verified;
- Windows dual-boot scenario tested before claiming compatibility.

## Gate D — system lifecycle
- signed/integrity-checked updates;
- rollback/recovery tested;
- security update procedure documented;
- SBOM and license review.

## Gate E — hardware/release
- representative hardware matrix;
- graphics, Wi-Fi, Bluetooth, audio, suspend/resume;
- release notes and known issues;
- only then consider an installation-ready release candidate.
