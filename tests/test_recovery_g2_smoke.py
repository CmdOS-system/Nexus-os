"""Tests for the standalone smoke command and its result contract."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from recovery_g2.smoke import smoke_test


class SmokeTests(unittest.TestCase):
    def test_smoke_uses_private_paths_and_never_claims_boot(self):
        def fake_create(args, **kwargs):
            Path(args[-2]).write_bytes(bytes.fromhex("514649fb") + b"fixture")
            return SimpleNamespace(returncode=0)
        with patch("recovery_g2.smoke.shutil.which", return_value="/usr/bin/qemu-img"), \
             patch("recovery_g2.smoke.subprocess.run", side_effect=fake_create), \
             patch("recovery_g2.smoke.validate_qcow2",
                   return_value={"format": "qcow2", "virtual_size": 64 * 1024**2}), \
             patch("recovery_g2.qcow2_isolation.validate_qcow2",
                   return_value={"format": "qcow2", "virtual_size": 64 * 1024**2}), \
             patch("recovery_g2.qemu_launch.validate_qcow2",
                   return_value={"format": "qcow2", "virtual_size": 64 * 1024**2}):
            result = smoke_test()
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["launch_plan_created"])
        self.assertIs(result["vm_booted"], False)

    def test_missing_qemu_img_is_reported(self):
        with patch("recovery_g2.smoke.shutil.which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "qemu-img is required"):
                smoke_test()
