"""Execute an actual UEFI guest and require the QEMU debug-exit marker."""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .guest_marker import SUCCESS_EXIT_CODE, classify_guest_exit
from .ovmf_isolation import isolated_ovmf_vars


def run_efi_probe(efi_binary, *, timeout=45):
    for tool in ("qemu-system-x86_64", "mkfs.vfat", "mmd", "mcopy"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"required tool not found: {tool}")
    binary = Path(efi_binary).resolve(strict=True)
    if not binary.is_file() or binary.stat().st_size == 0:
        raise ValueError("EFI binary must be a nonempty file")
    firmware_pairs = [
        ("/usr/share/OVMF/OVMF_CODE_4M.fd", "/usr/share/OVMF/OVMF_VARS_4M.fd"),
        ("/usr/share/OVMF/OVMF_CODE.fd", "/usr/share/OVMF/OVMF_VARS.fd"),
    ]
    firmware = next(((Path(a), Path(b)) for a, b in firmware_pairs
                     if Path(a).is_file() and Path(b).is_file()), None)
    if firmware is None:
        raise RuntimeError("OVMF firmware pair unavailable")
    with tempfile.TemporaryDirectory(prefix="nexus-efi-boot-") as root:
        esp = Path(root) / "efi-fat.img"
        with esp.open("wb") as out:
            out.truncate(64 * 1024 * 1024)
        subprocess.run(["mkfs.vfat", "-F", "16", str(esp)], check=True,
                       capture_output=True, timeout=30)
        subprocess.run(["mmd", "-i", str(esp), "::/EFI", "::/EFI/BOOT"],
                       check=True, capture_output=True, timeout=30)
        subprocess.run(["mcopy", "-i", str(esp), str(binary),
                        "::/EFI/BOOT/BOOTX64.EFI"], check=True,
                       capture_output=True, timeout=30)
        with isolated_ovmf_vars(firmware[1], lab_root=root) as vars_copy:
            argv = [
                "qemu-system-x86_64", "-machine", "q35", "-accel", "tcg",
                "-m", "512", "-nic", "none", "-display", "none",
                "-monitor", "none", "-serial", "none", "-no-reboot",
                "-drive", f"if=pflash,format=raw,readonly=on,file={firmware[0]}",
                "-drive", f"if=pflash,format=raw,file={vars_copy}",
                "-drive", f"if=ide,format=raw,file={esp}",
                "-device", "isa-debug-exit,iobase=0xf4,iosize=0x04",
            ]
            try:
                result = subprocess.run(argv, capture_output=True, text=True,
                                        timeout=timeout, check=False)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("EFI guest did not emit marker before timeout") from exc
            classification = classify_guest_exit(result.returncode)
            if result.returncode != SUCCESS_EXIT_CODE:
                raise RuntimeError(f"EFI guest boot not confirmed: {classification}; "
                                   f"QEMU stderr: {result.stderr[-1200:]}")
            return {"status": "efi_guest_executed", "guest_marker_seen": True,
                    "os_booted": False, "qemu_exit_code": result.returncode}


if __name__ == "__main__":
    print(json.dumps(run_efi_probe("build/efi_probe/BOOTX64.EFI"), sort_keys=True))
