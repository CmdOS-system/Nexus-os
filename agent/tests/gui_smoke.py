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
            assert app.choice["state"] == "readonly"
            assert "/dev/vdb" in app.choice["values"]
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
    print("Nexus installer GUI smoke passed (no disk writes).")


if __name__ == "__main__":
    run()
