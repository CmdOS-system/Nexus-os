"""Nexus OS installation readiness report (read-only; never opens a disk).

Usage: python3 installer_preflight.py --json
       python3 installer_preflight.py --target /dev/vdb --json
Exit status: 0 if the selected target is eligible, 2 otherwise.
The report is advisory and is NOT authorization to erase a device.
"""
from __future__ import annotations

import argparse
import json
import sys
from installer_inventory import capture_inventory
from installer_plan import UnsafeTarget, plan_install


def inspect(inventory: dict, target: str | None = None) -> dict:
    """Return deterministic, non-destructive readiness findings for whole disks."""
    if not isinstance(inventory, dict) or not isinstance(inventory.get("blockdevices"), list):
        raise UnsafeTarget("invalid block-device inventory")
    candidates = inventory["blockdevices"]
    if not all(isinstance(d, dict) for d in candidates):
        raise UnsafeTarget("invalid disk inventory")
    paths = sorted({d.get("path") for d in candidates if d.get("type") == "disk" and isinstance(d.get("path"), str)})
    if target is not None and target not in paths:
        paths.append(target)
        paths.sort()
    findings = []
    for path in paths:
        try:
            plan = plan_install(inventory, path)
            findings.append({"path": path, "eligible": True, "size_bytes": plan.size_bytes,
                             "model": plan.model, "serial": plan.serial, "warning": plan.warning})
        except UnsafeTarget as exc:
            findings.append({"path": path, "eligible": False, "reason": str(exc)})
    return {"schema_version": 1, "mode": "read-only", "installation_enabled": False,
            "target": target, "target_eligible": any(f["path"] == target and f["eligible"] for f in findings)
            if target is not None else None, "disks": findings}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Nexus OS installation preflight")
    parser.add_argument("--target", help="Explicit /dev/ whole-disk target")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args(argv)
    try:
        report = inspect(capture_inventory(), args.target)
    except UnsafeTarget as exc:
        report = {"schema_version": 1, "mode": "read-only", "installation_enabled": False,
                  "target": args.target, "target_eligible": False, "disks": [], "error": str(exc)}
    if args.json:
        print(json.dumps(report, sort_keys=True, indent=2))
    else:
        print("Nexus OS — read-only installation readiness")
        for disk in report["disks"]:
            print(f"{disk['path']}: {'ELIGIBLE FOR PREVIEW' if disk['eligible'] else 'REJECTED'}")
            if not disk["eligible"]:
                print(f"  Reason: {disk['reason']}")
        if "error" in report:
            print(f"Inventory error: {report['error']}")
        print("Installation is DISABLED; no disk changes were made.")
    return 0 if args.target and report["target_eligible"] else 2


if __name__ == "__main__":
    sys.exit(main())
