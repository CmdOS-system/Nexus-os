"""Command-line smoke test for Nexus OS Recovery G2 QCOW2 lab.

Requires qemu-img and creates only temporary, disposable fixtures.
No VM is launched.
"""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .qcow2_validate import validate_qcow2
from .qemu_lab import isolated_launch_plan


def smoke_test():
    if shutil.which("qemu-img") is None:
        raise RuntimeError("qemu-img is required; install qemu-utils")
    with tempfile.TemporaryDirectory(prefix="nexus-smoke-") as root:
        folder = Path(root)
        disk = folder / "source.qcow2"
        code = folder / "CODE.fd"
        vars_template = folder / "VARS.fd"
        code.write_bytes(b"QEMU command planning fixture only")
        vars_template.write_bytes(b"OVMF variable planning fixture only")
        subprocess.run(["qemu-img", "create", "-f", "qcow2", str(disk), "64M"],
                       capture_output=True, text=True, check=True, timeout=30)
        validated = validate_qcow2(disk)
        with isolated_launch_plan(qemu_binary="qemu-system-x86_64",
                                  firmware_code=code,
                                  firmware_vars_template=vars_template,
                                  disk_image=disk,
                                  lab_root=folder) as argv:
            if not any(arg.startswith("if=virtio,format=qcow2,file=") for arg in argv):
                raise RuntimeError("QEMU plan lacks isolated QCOW2 disk")
            if not any(arg.startswith("if=pflash,format=raw,file=") for arg in argv):
                raise RuntimeError("QEMU plan lacks isolated OVMF variables")
            result = {"status": "passed", "disk_format": validated["format"],
                      "virtual_size": validated["virtual_size"],
                      "launch_plan_created": True, "vm_booted": False}
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(smoke_test(), sort_keys=True))


if __name__ == "__main__":
    main()
