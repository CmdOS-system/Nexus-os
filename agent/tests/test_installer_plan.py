import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from installer_plan import UnsafeTarget, plan_install


class InstallerPlanTests(unittest.TestCase):
    def inventory(self):
        return {"blockdevices": [{
            "path": "/dev/vdb", "type": "disk", "size": 32 * 1024**3,
            "serial": "DISPOSABLE-TEST-DISK", "model": "QEMU",
            "ro": False, "rm": False, "mountpoints": [None],
            "children": [{"path": "/dev/vdb1", "type": "part", "mountpoints": [None]}],
        }]}

    def test_dry_run_returns_warning(self):
        plan = plan_install(self.inventory(), "/dev/vdb")
        self.assertEqual(plan.serial, "DISPOSABLE-TEST-DISK")
        self.assertIn("WOULD BE ERASED", plan.warning)

    def test_rejects_partition_target(self):
        with self.assertRaises(UnsafeTarget):
            plan_install(self.inventory(), "/dev/vdb1")

    def test_rejects_mounted_child(self):
        inventory = self.inventory()
        inventory["blockdevices"][0]["children"][0]["mountpoints"] = ["/"]
        with self.assertRaises(UnsafeTarget):
            plan_install(inventory, "/dev/vdb")

    def test_rejects_unknown_mount_status(self):
        inventory = self.inventory()
        del inventory["blockdevices"][0]["children"][0]["mountpoints"]
        with self.assertRaises(UnsafeTarget):
            plan_install(inventory, "/dev/vdb")

    def test_rejects_missing_serial(self):
        inventory = self.inventory()
        inventory["blockdevices"][0]["serial"] = None
        with self.assertRaises(UnsafeTarget):
            plan_install(inventory, "/dev/vdb")

    def test_rejects_readonly(self):
        inventory = self.inventory()
        inventory["blockdevices"][0]["ro"] = True
        with self.assertRaises(UnsafeTarget):
            plan_install(inventory, "/dev/vdb")

    def test_rejects_undersized(self):
        inventory = self.inventory()
        inventory["blockdevices"][0]["size"] = 2 * 1024**3
        with self.assertRaises(UnsafeTarget):
            plan_install(inventory, "/dev/vdb")

    def test_rejects_duplicate_child_path(self):
        inventory = self.inventory()
        inventory["blockdevices"][0]["children"].append(
            {"path": "/dev/vdb1", "type": "part", "mountpoints": [None]}
        )
        with self.assertRaises(UnsafeTarget):
            plan_install(inventory, "/dev/vdb")

    def test_rejects_missing_child_path(self):
        inventory = self.inventory()
        del inventory["blockdevices"][0]["children"][0]["path"]
        with self.assertRaises(UnsafeTarget):
            plan_install(inventory, "/dev/vdb")

    def test_rejects_ambiguous_identity(self):
        inventory = self.inventory()
        inventory["blockdevices"].append(dict(inventory["blockdevices"][0]))
        with self.assertRaises(UnsafeTarget):
            plan_install(inventory, "/dev/vdb")


if __name__ == "__main__":
    unittest.main()
