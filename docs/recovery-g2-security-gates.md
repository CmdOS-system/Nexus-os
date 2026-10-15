"""Recovery G2 operational safety notes and validation checklist.

The current controller is a prototype. It MUST NOT be invoked as a privileged
bootloader hook or used to write real OS partitions.
"""

## Trust boundaries

- `stage_verified(authenticated=True, image_durable=True)` accepts assertions from
  its caller; it does not verify cryptographic signatures or image contents.
- SHA-256 checksums in metadata detect accidental corruption, not adversarial tampering.
- A verified image must be authenticated against a trusted key, checked for platform
  compatibility, and flushed to the inactive partition before staging.
- `prepare_boot()` persists a retry decrement before returning a slot name. A real
  boot manager still needs to consume that decision atomically and safely.
- A health confirmation must come from a trusted userspace health service, not an
  untrusted application.
- The file store is not safe for concurrent writers; serialize all transactions
  with an OS-level lock before using it outside single-process simulations.
- The storage prototype is not hardened against symlink attacks or hostile
  directory permissions. Use a dedicated root-owned protected directory in any
  future integration.

## Validation gates before hardware testing

1. Run `python -m unittest discover -s tests -p 'test_recovery_g2_*.py' -v`.
2. Check the GitHub Actions run and retain the job URL and result.
3. Add crash-injection tests at every atomic replace/fsync boundary.
4. Validate rollback with disposable QEMU/OVMF virtual disks.
5. Verify signatures, secure boot chain, bootloader integration and partition isolation.
6. Confirm user data is stored outside replaceable A/B system slots.
7. Conduct physical hardware tests only after virtual-machine gates pass.

Do not install this prototype on a primary computer.
