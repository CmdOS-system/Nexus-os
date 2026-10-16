"""Read-only lsblk inventory capture for the Nexus installation planner.

No disk writes, mounting, or privileged installer actions are performed.
"""
from __future__ import annotations

import json
import subprocess

from installer_plan import UnsafeTarget

# Explicit columns and --tree are necessary for reliable children[] in JSON.
LSBLK_COMMAND = (
    "lsblk", "--json", "--bytes", "--tree",
    "--output", "NAME,PATH,TYPE,SIZE,MODEL,SERIAL,TRAN,MOUNTPOINTS,RO,RM",
)


def capture_inventory(*, timeout: float = 10.0) -> dict:
    """Capture a snapshot only; caller must recheck before any future writes."""
    try:
        completed = subprocess.run(
            LSBLK_COMMAND, capture_output=True, text=True, check=True,
            timeout=timeout, stdin=subprocess.DEVNULL,
        )
        inventory = json.loads(completed.stdout)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired,
            UnicodeError, json.JSONDecodeError) as exc:
        raise UnsafeTarget("cannot obtain trustworthy disk inventory") from exc
    if not isinstance(inventory, dict) or not isinstance(inventory.get("blockdevices"), list):
        raise UnsafeTarget("invalid lsblk JSON inventory")
    return inventory


def require_unchanged_inventory(previous: dict, current: dict) -> dict:
    """Fail closed if a read-only inventory snapshot changed between UI steps."""
    if not isinstance(previous, dict) or not isinstance(current, dict):
        raise UnsafeTarget("disk inventory snapshot is invalid")
    if not isinstance(previous.get("blockdevices"), list) or not isinstance(current.get("blockdevices"), list):
        raise UnsafeTarget("disk inventory snapshot is invalid")
    if previous != current:
        raise UnsafeTarget("disk inventory changed; refresh and select the target again")
    return current
