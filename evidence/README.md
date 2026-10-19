# Nexus visual evidence

This directory stores evidence produced by automated guest and application smoke tests.

- `boot/desktop-boot.png` — PNG framebuffer capture of the XFCE session from the QEMU UEFI boot smoke test.
- `windows/` — Windows application and Wine screenshots.
- `android/` — Android and Waydroid screenshots.
- `web/` — browser and web application screenshots.
- `ios/ipa-running.png` — IPA metadata and ARM64 Mach-O inspection response in XFCE; its structural fixture is not executed.

The ISO Gate uploads serial and QEMU debug logs, extracted GRUB configuration, and desktop/application PNG evidence from its smoke tests.
