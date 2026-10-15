"""Regression tests for bounded real-OVMF probe orchestration."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from recovery_g2.ovmf_probe import probe_ovmf


class OvmfProbeTests(unittest.TestCase):
    def test_rejects_invalid_timeout_before_starting_tools(self):
        for seconds in (True, 0, 61, "8", None):
            with self.subTest(seconds=seconds):
                with self.assertRaises(ValueError):
                    probe_ovmf(seconds=seconds)

    def test_missing_qemu_is_actionable(self):
        with patch("recovery_g2.ovmf_probe.shutil.which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "required"):
                probe_ovmf()

    def test_qemu_early_exit_fails_instead_of_claiming_success(self):
        with tempfile.TemporaryDirectory() as folder:
            code = Path(folder) / "CODE.fd"
            vars_ = Path(folder) / "VARS.fd"
            code.write_bytes(b"firmware")
            vars_.write_bytes(b"vars")
            with patch("recovery_g2.ovmf_probe.shutil.which", return_value="/usr/bin/tool"), \
                 patch("recovery_g2.ovmf_probe.Path.is_file", return_value=True), \
                 patch("recovery_g2.ovmf_probe.Path.stat") as stat, \
                 patch("recovery_g2.ovmf_probe.subprocess.run") as run, \
                 patch("recovery_g2.ovmf_probe.isolated_launch_plan") as plan:
                stat.return_value.st_size = 1024
                run.side_effect = [subprocess.CompletedProcess([], 0),
                                   subprocess.CompletedProcess([], 1, "", "firmware failure")]
                plan.return_value.__enter__.return_value = ["qemu-system-x86_64"]
                with self.assertRaisesRegex(RuntimeError, "firmware failure"):
                    probe_ovmf(seconds=2)

    def test_timeout_reports_only_power_on_not_os_boot(self):
        with tempfile.TemporaryDirectory():
            with patch("recovery_g2.ovmf_probe.shutil.which", return_value="/usr/bin/tool"), \
                 patch("recovery_g2.ovmf_probe.Path.is_file", return_value=True), \
                 patch("recovery_g2.ovmf_probe.Path.stat") as stat, \
                 patch("recovery_g2.ovmf_probe.subprocess.run") as run, \
                 patch("recovery_g2.ovmf_probe.isolated_launch_plan") as plan:
                stat.return_value.st_size = 1024
                run.side_effect = [subprocess.CompletedProcess([], 0),
                                   subprocess.TimeoutExpired(["qemu"], 2)]
                plan.return_value.__enter__.return_value = ["qemu-system-x86_64"]
                result = probe_ovmf(seconds=2)
                self.assertIs(result["os_booted"], False)
                self.assertEqual(result["firmware_power_on_probe"], "inconclusive")
