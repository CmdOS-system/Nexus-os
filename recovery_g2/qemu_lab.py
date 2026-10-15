"""Disposable QEMU/OVMF launch context; never executes QEMU.

Callers must keep the context open until the guest process exits.
"""
from contextlib import contextmanager
from pathlib import Path

from .ovmf_isolation import isolated_ovmf_vars
from .qcow2_isolation import isolated_qcow2_disk
from .qemu_launch import build_launch_plan

@contextmanager
def isolated_launch_plan(*, qemu_binary, firmware_code, firmware_vars_template,
                         disk_image, memory_mb=2048, lab_root=None):
    """Yield QEMU argv with a private, automatically cleaned OVMF VARS copy.

    Both OVMF variables and QCOW2 disk are private disposable copies.
    """
    with isolated_ovmf_vars(firmware_vars_template, lab_root=lab_root) as vars_copy:
        with isolated_qcow2_disk(disk_image, lab_root=lab_root) as disk_copy:
            argv = build_launch_plan(
                qemu_binary=qemu_binary,
                firmware_code=firmware_code,
                firmware_vars=vars_copy,
                disk_image=disk_copy,
                memory_mb=memory_mb,
            )
            yield argv
