import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from installer_preflight import inspect, main
from installer_plan import UnsafeTarget


def disk(path, serial, mounted=False):
    return {"path": path, "name": path.rsplit("/", 1)[-1], "type": "disk",
            "size": 20 * 1024**3, "serial": serial, "model": "Virtual disk",
            "ro": False, "rm": False, "mountpoints": ["/" if mounted else None],
            "children": []}


class PreflightTests(unittest.TestCase):
    def test_safe_and_mounted_disks_are_reported_without_writes(self):
        inventory = {"blockdevices": [disk("/dev/vdc", "MOUNTED", True), disk("/dev/vdb", "SAFE")]}
        report = inspect(inventory, "/dev/vdb")
        self.assertFalse(report["installation_enabled"])
        self.assertEqual(report["mode"], "read-only")
        self.assertTrue(report["target_eligible"])
        self.assertEqual([d["path"] for d in report["disks"]], ["/dev/vdb", "/dev/vdc"])
        self.assertFalse(next(d for d in report["disks"] if d["path"] == "/dev/vdc")["eligible"])
        self.assertIn("mounted", report["disks"][1]["reason"])

    def test_missing_target_rejected(self):
        report = inspect({"blockdevices": [disk("/dev/vdb", "SAFE")]}, "/dev/does-not-exist")
        self.assertFalse(report["target_eligible"])
        self.assertFalse(next(d for d in report["disks"] if d["path"] == "/dev/does-not-exist")["eligible"])

    def test_invalid_inventory_rejected(self):
        with self.assertRaises(UnsafeTarget):
            inspect({"blockdevices": [None]})

    @patch("installer_preflight.capture_inventory")
    def test_cli_json_and_exit_status(self, capture):
        capture.return_value = {"blockdevices": [disk("/dev/vdb", "SAFE")]}
        from contextlib import redirect_stdout
        from io import StringIO
        import json
        output = StringIO()
        with redirect_stdout(output):
            code = main(["--target", "/dev/vdb", "--json"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())["target_eligible"])
        with redirect_stdout(StringIO()):
            self.assertEqual(main(["--target", "/dev/vdc", "--json"]), 2)

    @patch("installer_preflight.capture_inventory", side_effect=UnsafeTarget("lsblk failed"))
    def test_cli_fails_closed(self, capture):
        from contextlib import redirect_stdout
        from io import StringIO
        import json
        output = StringIO()
        with redirect_stdout(output):
            code = main(["--target", "/dev/vdb", "--json"])
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(output.getvalue())["installation_enabled"])


if __name__ == "__main__":
    unittest.main()
