"""Integration checks against actual qemu-img, not mocked metadata.

Run on a Linux runner with qemu-utils installed.
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from recovery_g2.qcow2_validate import validate_qcow2
from recovery_g2.qemu_lab import isolated_launch_plan

@unittest.skipUnless(shutil.which("qemu-img"), "qemu-img is required")
class RealQcow2IntegrationTests(unittest.TestCase):
    def test_real_image_is_validated_and_isolated(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            disk = root / "source.qcow2"
            code = root / "CODE.fd"
            variables = root / "VARS.fd"
            code.write_bytes(b"fixture firmware code")
            variables.write_bytes(b"fixture variables")
            subprocess.run(["qemu-img", "create", "-f", "qcow2", str(disk), "64M"],
                           check=True, capture_output=True, timeout=30)
            self.assertEqual(validate_qcow2(disk)["virtual_size"], 64 * 1024**2)
            with isolated_launch_plan(qemu_binary="qemu-system-x86_64",
                                      firmware_code=code,
                                      firmware_vars_template=variables,
                                      disk_image=disk,
                                      lab_root=root) as argv:
                guest = Path(next(v.split("file=", 1)[1] for v in argv
                                  if v.startswith("if=virtio,format=qcow2,file=")))
                guest_vars = Path(next(v.split("file=", 1)[1] for v in argv
                                       if v.startswith("if=pflash,format=raw,file=")))
                self.assertNotEqual(guest, disk)
                self.assertNotEqual(guest_vars, variables)
                self.assertTrue(guest.exists())
                self.assertTrue(guest_vars.exists())
                self.assertEqual(validate_qcow2(guest)["virtual_size"], 64 * 1024**2)
            self.assertFalse(guest.exists())
            self.assertFalse(guest_vars.exists())
            self.assertTrue(disk.exists())
            self.assertEqual(variables.read_bytes(), b"fixture variables")

    def test_rejects_real_backing_chain(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder) / "base.qcow2"
            child = Path(folder) / "child.qcow2"
            subprocess.run(["qemu-img", "create", "-f", "qcow2", str(base), "64M"],
                           check=True, capture_output=True, timeout=30)
            subprocess.run(["qemu-img", "create", "-f", "qcow2",
                            "-F", "qcow2", "-b", str(base), str(child)],
                           check=True, capture_output=True, timeout=30)
            with self.assertRaisesRegex(ValueError, "backing"):
                validate_qcow2(child)
