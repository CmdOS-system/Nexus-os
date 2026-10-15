"""Read-only QEMU/OVMF environment preflight for Nexus OS.

No VM is started, no disks are created, and no privileged commands are run.
"""
import json
import os
import shutil
from pathlib import Path

OVMF_CANDIDATES = (
    ("/usr/share/OVMF/OVMF_CODE_4M.fd", "/usr/share/OVMF/OVMF_VARS_4M.fd"),
    ("/usr/share/OVMF/OVMF_CODE.fd", "/usr/share/OVMF/OVMF_VARS.fd"),
    ("/usr/share/edk2/ovmf/OVMF_CODE.fd", "/usr/share/edk2/ovmf/OVMF_VARS.fd"),
)

def preflight(which=shutil.which, exists=os.path.isfile):
    commands = {name: which(name) for name in
                ("qemu-system-x86_64", "qemu-img", "bootctl", "systemd-bless-boot")}
    firmware = next(((code, vars_) for code, vars_ in OVMF_CANDIDATES
                     if exists(code) and exists(vars_)), None)
    return {"commands": commands,
            "ovmf_code": None if firmware is None else firmware[0],
            "ovmf_vars_template": None if firmware is None else firmware[1],
            "ready_for_vm_setup": bool(commands["qemu-system-x86_64"] and
                                       commands["qemu-img"] and firmware)}

if __name__ == "__main__":
    print(json.dumps(preflight(), indent=2))
