"""Validate QEMU image metadata; rejects external backing chains."""
import json
import subprocess
from pathlib import Path

def validate_qcow2(path, *, qemu_img="qemu-img", runner=subprocess.run):
    image = Path(path).resolve(strict=True)
    if not image.is_file():
        raise ValueError("disk must be a regular file")
    with image.open("rb") as stream:
        if stream.read(4) != bytes.fromhex("514649fb"):
            raise ValueError("invalid QCOW2 signature")
    result = runner([qemu_img, "info", "--output=json", "-f", "qcow2", str(image)],
                    capture_output=True, text=True, check=True, timeout=15)
    metadata = json.loads(result.stdout)
    if not isinstance(metadata, dict) or metadata.get("format") != "qcow2":
        raise ValueError("qemu-img did not confirm QCOW2")
    if metadata.get("backing-filename") or metadata.get("full-backing-filename") or metadata.get("data-file") or metadata.get("encrypted") is True:
        raise ValueError("external backing/data files or encrypted images are forbidden in isolated lab")
    size = metadata.get("virtual-size")
    if type(size) is not int or not 1024 * 1024 <= size <= 128 * 1024**3:
        raise ValueError("virtual size outside lab limits")
    check = runner([qemu_img, "check", "--output=json", "-f", "qcow2", str(image)],
                   capture_output=True, text=True, check=True, timeout=60)
    report = json.loads(check.stdout)
    if not isinstance(report, dict) or report.get("corruptions", 0) != 0 or report.get("leaks", 0) != 0 or report.get("check-errors", report.get("check_errors", 0)) != 0:
        raise ValueError("QCOW2 consistency check failed")
    return {"format": "qcow2", "virtual_size": size}
