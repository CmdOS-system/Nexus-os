import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from recovery_g2.qemu_lab import isolated_launch_plan

class QemuLabTests(unittest.TestCase):
    def test_vars_copy_lifecycle_and_arguments(self):
        with tempfile.TemporaryDirectory() as root:
            paths = [Path(root) / n for n in ("CODE.fd", "VARS.fd", "disk.qcow2")]
            for p in paths[:2]:
                p.write_bytes(b"firmware fixture")
            paths[2].write_bytes(bytes.fromhex("514649fb") + b"fixture")
            with patch("recovery_g2.qemu_launch.validate_qcow2",
                       return_value={"format": "qcow2", "virtual_size": 1024**3}):
                with isolated_launch_plan(qemu_binary="qemu-system-x86_64",
                                          firmware_code=paths[0],
                                          firmware_vars_template=paths[1],
                                          disk_image=paths[2],
                                          lab_root=root) as argv:
                    vars_arg = next(v for v in argv if v.startswith("if=pflash,format=raw,file="))
                    private = Path(vars_arg.split("file=", 1)[1])
                    self.assertNotEqual(private, paths[1])
                    self.assertTrue(private.exists())
                    private.write_bytes(b"changed by guest")
                    self.assertEqual(paths[1].read_bytes(), b"firmware fixture")
                self.assertFalse(private.exists())

    def test_validation_failure_cleans_temporary_vars(self):
        with tempfile.TemporaryDirectory() as root:
            paths = [Path(root) / n for n in ("CODE.fd", "VARS.fd", "disk.qcow2")]
            for p in paths:
                p.write_bytes(b"invalid")
            with self.assertRaisesRegex(ValueError, "invalid QCOW2"):
                with isolated_launch_plan(qemu_binary="qemu", firmware_code=paths[0],
                                          firmware_vars_template=paths[1],
                                          disk_image=paths[2], lab_root=root):
                    pass
            self.assertEqual(sorted(p.name for p in Path(root).iterdir()),
                             sorted(p.name for p in paths))
