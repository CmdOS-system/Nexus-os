"""Bounded QEMU direct-Linux-boot probe.

A serial marker must be emitted by the guest's /init; kernel startup text
or a QEMU timeout alone never proves userspace initialization.
This is a direct kernel boot test, NOT proof of a UEFI boot chain.
"""
import json
import shutil
import subprocess
from pathlib import Path

MARKER = "NEXUS_LINUX_INIT_READY"


def probe_linux(kernel, initramfs, *, timeout=60, runner=subprocess.run):
    if type(timeout) is not int or not 1 <= timeout <= 180:
        raise ValueError("timeout must be an integer between 1 and 180")
    if shutil.which("qemu-system-x86_64") is None:
        raise RuntimeError("qemu-system-x86_64 is required")
    paths = [Path(p).resolve(strict=True) for p in (kernel, initramfs)]
    for path in paths:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError("kernel and initramfs must be nonempty files")
    argv = [
        "qemu-system-x86_64", "-machine", "q35", "-accel", "tcg",
        "-m", "512", "-smp", "1", "-nic", "none", "-display", "none",
        "-monitor", "none", "-serial", "stdio", "-no-reboot",
        "-kernel", str(paths[0]), "-initrd", str(paths[1]),
        "-append", "console=ttyS0 rdinit=/init panic=-1",
    ]
    try:
        result = runner(argv, capture_output=True, text=True, timeout=timeout,
                        check=False)
    except subprocess.TimeoutExpired as exc:
        # Python includes partial captured output in TimeoutExpired.stdout.
        output = exc.stdout or b""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        if MARKER not in output.splitlines():
            raise RuntimeError("Linux guest did not emit init marker before timeout") from exc
        return {"linux_init_confirmed": True, "uefi_boot_confirmed": False,
                "evidence": "guest_serial_marker"}
    if MARKER not in result.stdout.splitlines():
        raise RuntimeError(f"Linux init marker absent; QEMU exited {result.returncode}; "
                           f"serial tail: {result.stdout[-1000:]}; "
                           f"QEMU stderr: {result.stderr[-1200:]}")
    return {"linux_init_confirmed": True, "uefi_boot_confirmed": False,
            "evidence": "guest_serial_marker"}


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: python -m recovery_g2.linux_boot_probe KERNEL INITRAMFS")
    print(json.dumps(probe_linux(sys.argv[1], sys.argv[2]), sort_keys=True))
