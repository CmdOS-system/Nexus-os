# Nexus OS build and verification procedure

Status reviewed: 2026-10-16. Experimental Live system; not installation-ready, certified, or qualified on physical hardware.

## Verified evidence

- [ISO Gate 38935133161](https://github.com/CmdOS-system/Nexus-os/actions/runs/38935133161), commit `102704419534f0d6d65dec0764cfc76b833c9423`: Debian Trixie build, ISO artifact validation, checksum verification, final GRUB configuration inspection, QEMU/OVMF UEFI readiness smoke, and candidate/diagnostic uploads completed successfully.
- The boot smoke requires Live readiness, graphical-stack readiness and XFCE user-session markers. This is evidence of guest readiness, not visual quality, installation, persistence, network functionality or hardware qualification.
- [Fast Checks 38977578555](https://github.com/CmdOS-system/Nexus-os/actions/runs/38977578555), commit `378a6388974505059d7b1d3cc6640eda6d431d7e`: Python 3.12 and 3.13, graphical smoke, image static validation and installer runtime staging jobs all passed after correcting the Horizon smoke syntax error.
- These runs validate their respective commits; they do not establish reproducibility across independent builds or every release gate.

## Prerequisites

Use a disposable Debian 13 (trixie) amd64 builder with sufficient disk and memory. Build tooling includes live-build, xorriso and squashfs-tools; UEFI smoke requires qemu-system-x86 and OVMF. The ISO workflow builds in a privileged Debian container on an isolated CI runner; do not run it against a primary workstation without an appropriately isolated builder.

## Build

Run `bash verify.sh` and `bash image/validate.sh` before `sudo bash image/build.sh` on the disposable builder. Outputs are under `image/work/`. Run `bash image/verify-artifact.sh image/work` and verify `SHA256SUMS` before distributing. See `.github/workflows/nexus-iso-gate.yml` for the CI procedure.

## VM validation

Run `bash image/boot-smoke.sh /path/to/candidate.iso` with OVMF installed. Preserve serial logs and associate evidence with the exact commit and ISO checksum. Separately validate visible desktop interaction, network, shutdown/restart, BIOS where supported, and hardware behavior before claiming those capabilities.

The Live image remains non-installable. Installer planning/UI and staging checks do not establish disk installation. Destructive installer tests must use disposable virtual disks with no host block-device passthrough. Require installed-system boot without ISO, persistence, failure handling and recovery evidence before enabling installation; see `INSTALLER-ARCHITECTURE.md`.

## Release gates

Follow `release-gates.md`: reproducibility, installation, disk safety, updates/rollback, security, driver coverage, licenses and hardware qualification remain separate requirements. Passing a Live build/boot smoke does not satisfy all of them.

## AI integration

The repository contains prototype provider and policy modules. Their presence or unit tests do not prove a connected model, end-to-end desktop control, or production credential handling. Preserve explicit permissions, test provider integration separately and keep credentials out of source and logs. Security PR #1 was open and unmerged at this review; do not count its changes as delivered on main.

## Continuity

Read `PROJECT-CONTINUITY.md` for recovered requirements, verified progress and the next unresolved work.
