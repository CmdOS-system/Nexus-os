"""Create disposable firmware VARS copies for QEMU lab runs.

Never modifies the firmware template or any host EFI partition.
"""
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

@contextmanager
def isolated_ovmf_vars(template, *, lab_root=None):
    original = Path(template)
    if original.is_symlink():
        raise ValueError("symlinked OVMF VARS template is forbidden")
    source = original.resolve(strict=True)
    if not source.is_file():
        raise ValueError("OVMF VARS template must be a regular file")
    with tempfile.TemporaryDirectory(prefix="nexus-ovmf-", dir=lab_root) as directory:
        destination = Path(directory) / "OVMF_VARS.fd"
        with source.open("rb") as input_stream, destination.open("xb") as output_stream:
            shutil.copyfileobj(input_stream, output_stream)
            output_stream.flush()
            os.fsync(output_stream.fileno())
        destination.chmod(0o600)
        yield destination
