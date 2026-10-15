"""Disposable QCOW2 disk copy for isolated QEMU lab sessions.

This is a full byte copy, never a backing-file overlay.
"""
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

from .qcow2_validate import validate_qcow2

@contextmanager
def isolated_qcow2_disk(template, *, lab_root=None):
    source = Path(template)
    if source.is_symlink():
        raise ValueError("symlinked QCOW2 templates are forbidden")
    source = source.resolve(strict=True)
    if not source.is_file():
        raise ValueError("QCOW2 template must be a regular file")
    with source.open("rb") as stream:
        if stream.read(4) != bytes.fromhex("514649fb"):
            raise ValueError("invalid QCOW2 signature")
    validate_qcow2(source)
    with tempfile.TemporaryDirectory(prefix="nexus-disk-", dir=lab_root) as directory:
        destination = Path(directory) / "guest.qcow2"
        with source.open("rb") as reader, destination.open("xb") as writer:
            shutil.copyfileobj(reader, writer, length=1024 * 1024)
            writer.flush()
            os.fsync(writer.fileno())
        destination.chmod(0o600)
        validate_qcow2(destination)
        yield destination
