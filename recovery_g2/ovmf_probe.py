"""Run a bounded, disposable OVMF power-on probe.

This proves QEMU accepts the real firmware/disk configuration; it does not
prove a guest OS booted. The blank QCOW2 deliberately has no bootloader.
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .qemu_lab import isolated_launch_plan


def probe_ovmf(*, seconds=8):
    if type(seconds) not in (int, float) or not 2 <= seconds <= 60:
        raise ValueError("probe timeout must be 2..60 seconds")
    if shutil.which("qemu-system-x86_64") is None or shutil.which("qemu-img") is None:
        raise RuntimeError("qemu-system-x86_64 and qemu-img are required")
    pairs = [
        ("/usr/share/OVMF/OVMF_CODE_4M.fd", "/usr/share/OVMF/OVMF_VARS_4M.fd"),
        ("/usr/share/OVMF/OVMF_CODE.fd", "/usr/share/OVMF/OVMF_VARS.fd"),
    ]
    firmware = next(((Path(a), Path(b)) for a, b in pairs
                     if Path(a).is_file() and Path(b).is_file()
                     and Path(a).stat().st_size > 0 and Path(b).stat().st_size > 0), None)
    if firmware is None:
        raise RuntimeError("matching nonempty OVMF CODE/VARS firmware files not found")
    with tempfile.TemporaryDirectory(prefix="nexus-ovmf-probe-") as folder:
        disk = Path(folder) / "blank.qcow2"
        subprocess.run(["qemu-img", "create", "-f", "qcow2", str(disk), "64M"],
                       capture_output=True, text=True, check=True, timeout=30)
        with isolated_launch_plan(qemu_binary="qemu-system-x86_64",
                                  firmware_code=firmware[0],
                                  firmware_vars_template=firmware[1],
                                  disk_image=disk, memory_mb=512,
                                  lab_root=folder) as argv:
            # -display none and -serial stdio are already set by launch plan.
            # Disable networking, daemonization and acceleration in CI.
            debug_log = Path(folder) / "ovmf-debug.log"
            command = argv + ["-accel", "tcg", "-nic", "none", "-monitor", "none",
                              "-no-reboot", "-debugcon", f"file:{debug_log}",
                              "-global", "isa-debugcon.iobase=0x402"]
            try:
                result = subprocess.run(command, capture_output=True, text=True,
                                        timeout=seconds, check=False)
            except subprocess.TimeoutExpired:
                # A timeout only proves that the process did not exit; it is
                # not evidence that OVMF actually initialized successfully.
                size = debug_log.stat().st_size if debug_log.exists() else 0
                return {"status": "qemu_running_at_timeout",
                        "firmware_power_on_probe": "inconclusive",
                        "os_booted": False, "ovmf_debug_bytes": size}
            raise RuntimeError(
                "QEMU exited before probe timeout (exit=%s): %s" %
                (result.returncode, (result.stderr or result.stdout)[-1500:])
            )


if __name__ == "__main__":
    print(json.dumps(probe_ovmf(), sort_keys=True))
