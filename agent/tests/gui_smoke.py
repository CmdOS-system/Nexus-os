"""Headless Tk smoke: checks real widgets and read-only rejection behavior.
Run with: xvfb-run -a python3 agent/tests/gui_smoke.py
"""
import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agent"))
GUI = ROOT / "image/includes/opt/nexus/installer-preview.py"
spec = importlib.util.spec_from_file_location("nexus_installer_preview", GUI)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

INVENTORY = {"blockdevices": [{
    "name": "vdb", "path": "/dev/vdb", "type": "disk",
    "size": 20 * 1024 ** 3, "serial": "TEST-DISK-001",
    "model": "Virtual test disk", "ro": False, "rm": False,
    "mountpoints": [None], "children": [],
}]}


def run():
    with patch.object(module, "capture_inventory", return_value=INVENTORY):
        app = module.Preview()
        try:
            app.update_idletasks()
            assert app.winfo_exists()
            assert str(app.choice.cget("state")) == "readonly"
            assert "/dev/vdb" in app.choice["values"]
            assert "/dev/vdb: READY FOR PREVIEW" in app.result.get("1.0", "end")
            app.target.set("/dev/vdb")
            app.review()
            assert "Installation is DISABLED" in app.result.get("1.0", "end")
        finally:
            app.destroy()

    with patch.object(module, "capture_inventory", side_effect=[INVENTORY, {"blockdevices": []}]):
        app = module.Preview()
        try:
            app.target.set("/dev/vdb")
            app.review()
            assert not app.target.get()
            assert "inventory changed" in app.result.get("1.0", "end")
        finally:
            app.destroy()
    # A mounted disk must be visible as rejected with its reason, not silently omitted.
    mounted = {**INVENTORY["blockdevices"][0], "mountpoints": ["/mnt/test"]}
    with patch.object(module, "capture_inventory", return_value={"blockdevices": [mounted]}):
        app = module.Preview()
        try:
            output = app.result.get("1.0", "end")
            assert "/dev/vdb: REJECTED" in output
            assert "mounted" in output
        finally:
            app.destroy()

    # Inventory collection failure must not expose stale targets.
    with patch.object(module, "capture_inventory", side_effect=module.UnsafeTarget("simulated lsblk failure")):
        app = module.Preview()
        try:
            assert not app.choice["values"]
            assert not app.target.get()
            assert "Disk inventory unavailable" in app.result.get("1.0", "end")
        finally:
            app.destroy()

    # A previously selected disk must be cleared after refresh fails.
    with patch.object(module, "capture_inventory", side_effect=[INVENTORY, module.UnsafeTarget("device disappeared")]):
        app = module.Preview()
        try:
            app.target.set("/dev/vdb")
            app.refresh()
            assert not app.target.get()
            assert not app.choice["values"]
            assert "Disk inventory unavailable" in app.result.get("1.0", "end")
        finally:
            app.destroy()

    # An unsafe target must be rejected, and the previous selection invalidated.
    with (patch.object(module, "capture_inventory", return_value=INVENTORY),
          patch.object(module, "plan_install", side_effect=module.UnsafeTarget("unsafe simulated disk"))):
        app = module.Preview()
        try:
            app.target.set("/dev/vdb")
            app.review()
            assert not app.target.get()
            assert not app.choice["values"]
            assert "Target rejected" in app.result.get("1.0", "end")
            assert "No disk changes were made" in app.result.get("1.0", "end")
        finally:
            app.destroy()

    # The review must use a freshly captured snapshot and pass the selected target unchanged.
    with (patch.object(module, "capture_inventory", return_value=INVENTORY),
          patch.object(module, "plan_install") as planner):
        planner.return_value.path = "/dev/vdb"
        planner.return_value.model = "Virtual test disk"
        planner.return_value.serial = "TEST-DISK-001"
        planner.return_value.size_bytes = 20 * 1024 ** 3
        planner.return_value.warning = "Read-only preview"
        app = module.Preview()
        try:
            app.target.set("/dev/vdb")
            app.review()
            planner.assert_called_once_with(INVENTORY, "/dev/vdb")
            assert "Installation is DISABLED" in app.result.get("1.0", "end")
        finally:
            app.destroy()

    print("Nexus installer GUI smoke passed (no disk writes).")


if __name__ == "__main__":
    run()
