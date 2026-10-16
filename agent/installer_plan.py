"""Read-only, fail-closed Nexus OS installation planning primitives.

No disk is opened, mounted, formatted or modified by this module.
Callers supply an lsblk-style inventory; a privileged executor is NOT provided.
"""
from __future__ import annotations

from dataclasses import dataclass


class UnsafeTarget(ValueError):
    """The proposed installation target cannot be safely identified."""


@dataclass(frozen=True)
class InstallPlan:
    path: str
    size_bytes: int
    serial: str
    model: str
    warning: str


def _descendants(device: dict) -> list[dict]:
    result = [device]
    for child in device.get("children") or []:
        if not isinstance(child, dict):
            raise UnsafeTarget("invalid partition inventory")
        result.extend(_descendants(child))
    return result


def plan_install(inventory: dict, target_path: str) -> InstallPlan:
    """Validate an explicit whole-disk target without performing any I/O."""
    if not isinstance(inventory, dict) or not isinstance(inventory.get("blockdevices"), list):
        raise UnsafeTarget("invalid block-device inventory")
    if not isinstance(target_path, str) or not target_path.startswith("/dev/"):
        raise UnsafeTarget("an explicit /dev/ disk path is required")
    devices = inventory["blockdevices"]
    if not devices or any(not isinstance(d, dict) for d in devices):
        raise UnsafeTarget("invalid disk inventory")
    matches = [d for d in devices if d.get("path") == target_path]
    if len(matches) != 1:
        raise UnsafeTarget("target must match exactly one top-level disk")
    disk = matches[0]
    if disk.get("type") != "disk":
        raise UnsafeTarget("only whole disks may be selected")
    if disk.get("ro") not in (False, 0) or disk.get("rm") not in (False, 0):
        raise UnsafeTarget("read-only or removable disk rejected")
    size = disk.get("size")
    if type(size) is not int or size < 16 * 1024**3:
        raise UnsafeTarget("disk must be at least 16 GiB with an integer byte size")
    serial = disk.get("serial")
    if not isinstance(serial, str) or not serial.strip():
        raise UnsafeTarget("disk must have a stable nonempty serial")
    if sum(d.get("serial") == serial for d in devices) != 1:
        raise UnsafeTarget("duplicate disk serial")
    # Reject ambiguous inventory paths anywhere in the device tree.
    all_entries = [entry for root in devices for entry in _descendants(root)]
    paths = [entry.get("path") for entry in all_entries]
    if any(not isinstance(path, str) or not path.startswith("/dev/") for path in paths):
        raise UnsafeTarget("invalid or missing device path")
    if len(paths) != len(set(paths)):
        raise UnsafeTarget("duplicate device path")
    # Any active mount in the inventory must have an unambiguous parent chain.
    # Unknown mount data is never interpreted as a safe, unmounted device.
    for entry in all_entries:
        mounts = entry.get("mountpoints")
        if not isinstance(mounts, list):
            raise UnsafeTarget("mount status unknown in device inventory")
    # A mountpoint on the target disk or any child makes the disk unsafe.
    for entry in _descendants(disk):
        mounts = entry.get("mountpoints")
        if mounts is None:
            raise UnsafeTarget("mount status unknown")
        if not isinstance(mounts, list) or any(m is not None for m in mounts):
            raise UnsafeTarget("disk or partition is mounted")
    return InstallPlan(
        path=target_path,
        size_bytes=size,
        serial=serial.strip(),
        model=str(disk.get("model") or ""),
        warning=f"ALL DATA on {target_path} (serial {serial.strip()}) WOULD BE ERASED; dry run only.",
    )
