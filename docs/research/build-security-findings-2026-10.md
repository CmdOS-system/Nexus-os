# Nexus OS: build and security research notes (2026-10)

## Verified design references

- Debian Live Manual: package manifests belong in `config/package-lists/*.list.chroot`; files injected into the Live root filesystem belong in `config/includes.chroot`. Source: https://live-team.pages.debian.net/live-manual/html/live-manual.en.html
- QEMU system emulation provides the VM substrate; OVMF/UEFI firmware is an external dependency. Source: https://www.qemu.org/docs/master/system/index.html
- Flatpak offers application sandboxing, but permissions such as filesystem, network, sockets and D-Bus must be explicitly reviewed. Source: https://docs.flatpak.org/en/latest/flatpak-command-reference.html

## Engineering implications

1. Staging is now independently inspectable via `NEXUS_PREPARE_ONLY=1 bash image/build.sh` on a machine with live-build installed. This invokes `lb config` but deliberately skips `lb build`.
2. Never interpret ISO checksum verification or QEMU serial output as proof of a functioning desktop.
3. Do not run Nexus Agent with root privileges; any privileged operation must be mediated by a separate authorization broker.
4. Treat every AI provider response and tool request as untrusted. Provider configuration must never imply permission to access files or execute programs.
5. The initial CLI is a prototype, not a secure system administration agent.

## Outstanding validation

- Run source validation and agent unit tests in a controlled environment.
- Run prepare-only staging, inspect copied files and manifests.
- Run actual Debian trixie live-build with package download.
- Verify and boot ISO in a disposable QEMU guest.
- Add guest-visible boot milestone instrumentation before claiming automated boot success.
- Implement real desktop credential storage and provider onboarding.
