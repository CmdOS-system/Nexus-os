# Nexus OS identity

Nexus OS is currently a Debian-derived development distribution. The project must not hide or misrepresent that base.

The image carries a Nexus-specific metadata file at `/etc/nexus-os-release` plus console/release identity files. We intentionally do not overwrite Debian package-manager identity in a way that could break compatibility or make Debian tooling believe it is running on an unsupported base.

Current version: 0.1 development preview.

Before a stable release, versioning, update channels, signing identity, package origin and support lifecycle must be formally defined.
