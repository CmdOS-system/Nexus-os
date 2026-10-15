"""Safe, disposable QEMU/OVMF launch-plan builder.

This module only constructs commands. It does not execute them.
"""
import os
from pathlib import Path

def build_launch_plan(*, qemu_binary, firmware_code, firmware_vars,
                      disk_image, memory_mb=2048):
    for value in (qemu_binary, firmware_code, firmware_vars, disk_image):
        if not isinstance(value, (str, os.PathLike)) or not str(value):
            raise ValueError("all paths must be provided")
    if type(memory_mb) is not int or not 512 <= memory_mb <= 32768:
        raise ValueError("memory outside safe laboratory range")
    code = Path(firmware_code).resolve(strict=True)
    vars_ = Path(firmware_vars).resolve(strict=True)
    disk = Path(disk_image).resolve(strict=True)
    if not code.is_file() or not vars_.is_file() or not disk.is_file():
        raise ValueError("firmware and disk must be existing files")
    if disk in (code, vars_) or code == vars_:
        raise ValueError("firmware and disk paths must be distinct")
    if disk.is_block_device():
        raise ValueError("physical block devices are forbidden")
    return [
        str(qemu_binary), "-machine", "q35", "-m", str(memory_mb),
        "-drive", f"if=pflash,format=raw,readonly=on,file={code}",
        "-drive", f"if=pflash,format=raw,file={vars_}",
        "-drive", f"if=virtio,format=qcow2,file={disk}",
        "-boot", "menu=on", "-serial", "stdio", "-display", "none",
    ]
