# Nexus visual evidence

This directory stores evidence produced by automated guest and application smoke tests.

- `boot/desktop-boot.png` — PNG framebuffer capture of the XFCE session from the QEMU UEFI boot smoke test.
- `windows/` — Windows application and Wine screenshots.
- `android/` — Android and Waydroid screenshots.
- `web/` — browser and web application screenshots.

The ISO Gate currently publishes serial and QEMU debug logs plus the extracted GRUB configuration as boot diagnostics. It does not yet produce a desktop screenshot; the boot smoke test now saves and uploads `boot/desktop-boot.png`.
