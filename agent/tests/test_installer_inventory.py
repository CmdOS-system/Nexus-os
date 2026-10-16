import os
import sys
import subprocess
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from installer_inventory import LSBLK_COMMAND, capture_inventory
from installer_plan import UnsafeTarget


class InventoryTests(unittest.TestCase):
    @patch("installer_inventory.subprocess.run")
    def test_readonly_command_and_json(self, run):
        run.return_value.stdout = '{"blockdevices": []}'
        self.assertEqual(capture_inventory(), {"blockdevices": []})
        args, kwargs = run.call_args
        self.assertEqual(args[0], LSBLK_COMMAND)
        self.assertIn("--tree", args[0])
        self.assertIn("MOUNTPOINTS", args[0][-1])
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)

    @patch("installer_inventory.subprocess.run")
    def test_rejects_invalid_json(self, run):
        run.return_value.stdout = "not-json"
        with self.assertRaises(UnsafeTarget):
            capture_inventory()

    @patch("installer_inventory.subprocess.run")
    def test_rejects_command_failure(self, run):
        run.side_effect = subprocess.CalledProcessError(1, LSBLK_COMMAND)
        with self.assertRaises(UnsafeTarget):
            capture_inventory()

    @patch("installer_inventory.subprocess.run")
    def test_rejects_missing_devices(self, run):
        run.return_value.stdout = '{"unexpected": []}'
        with self.assertRaises(UnsafeTarget):
            capture_inventory()


if __name__ == "__main__":
    unittest.main()
