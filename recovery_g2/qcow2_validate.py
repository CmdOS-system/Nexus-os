"""Validate QEMU image metadata; rejects external backing chains."""
import json
import subprocess
from pathlib import Path

def validate_qcow2(path, *, qemu_img="qemu-img", runner=subprocess.run):
    image = Path(path).resolve(strict=True)
    if not image.is_file():
        raise ValueError("disk must be a regular file")
    with image.open("rb") as stream:
        header = stream.read(104)
    if header[:4] != bytes.fromhex("514649fb"):
        raise ValueError("invalid QCOW2 signature")
    if len(header) < 72:
        raise ValueError("truncated QCOW2 header")
    version = int.from_bytes(header[4:8], "big")
    if version not in (2, 3):
        raise ValueError("unsupported QCOW2 version")
    backing_offset = int.from_bytes(header[8:16], "big")
    backing_size = int.from_bytes(header[16:20], "big")
    if backing_offset or backing_size:
        raise ValueError("QCOW2 backing image is forbidden")
    crypt_method = int.from_bytes(header[32:36], "big")
    if crypt_method:
        raise ValueError("encrypted QCOW2 image is forbidden")
    if version == 3:
        if len(header) < 104:
            raise ValueError("truncated QCOW2 v3 header")
        header_length = int.from_bytes(header[100:104], "big")
        if header_length < 104 or header_length % 8:
            raise ValueError("invalid QCOW2 v3 header length")
        incompatible = int.from_bytes(header[72:80], "big")
        if incompatible & 0b11:
            raise ValueError("dirty or corrupt QCOW2 image is forbidden")
        if incompatible & (1 << 2):
            raise ValueError("external QCOW2 data file is forbidden")
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
    if not isinstance(report, dict):
        raise ValueError("QCOW2 consistency report is invalid")
    # QAPI ImageCheck omits optional zero-valued corruptions/leaks.
    # The subprocess exit code (check=True) independently guarantees that
    # qemu-img completed its check with no corruption or leaked clusters.
    for key in ("corruptions", "leaks"):
        count = report.get(key, 0)
        if type(count) is not int or count != 0:
            raise ValueError("QCOW2 consistency check failed")
    # ImageCheck requires check-errors; corruptions and leaks are optional.
    errors = report.get("check-errors", report.get("check_errors"))
    if type(errors) is not int or errors != 0:
        raise ValueError("QCOW2 consistency check failed")
    return {"format": "qcow2", "virtual_size": size}
