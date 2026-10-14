# Nexus OS ISO artifact verification

After a successful live-build run, execute:

`bash image/verify-artifact.sh image/work`

The verifier requires exactly one ISO in the artifact directory, a non-empty SHA256SUMS file, a valid checksum, and an artifact recognized as an ISO 9660 image.

Passing this check does **not** prove that the image boots or that Nexus OS is safe to install. It only promotes the output from an unverified build artifact to an ISO candidate ready for VM boot testing.

## Next gate

The next validation stage must boot the candidate in an isolated VM and verify firmware boot, desktop startup, networking, restart and shutdown. Disk installation remains disabled.
