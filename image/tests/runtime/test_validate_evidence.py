"""Regression tests for fail-closed Linux Flatpak X11 identity fallback."""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "nexus_evidence_validator", Path(__file__).with_name("validate-evidence.py"))
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class FlatpakOwnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.proc_root = Path(self.tmp.name)
        self.proc = self.proc_root / "4321"
        self.proc.mkdir()
        (self.proc / "comm").write_text("gnome-mines\n")
        (self.proc / "cmdline").write_bytes(b"/app/bin/gnome-mines\0")

    def check(self, wm_class="org.gnome.Mines org.gnome.Mines",
              output="org.gnome.Mines\t4321\n", returncode=0):
        result = subprocess.CompletedProcess([], returncode, output, "")
        with patch.object(validator.shutil, "which", return_value="/usr/bin/flatpak"), \
             patch.object(validator.subprocess, "run", return_value=result) as run:
            value = validator.linux_flatpak_owner(wm_class, self.proc_root)
            run.assert_called_once()
            return value

    def test_valid_flatpak_process(self):
        self.assertEqual(self.check(), 4321)

    def test_store_window_rejected(self):
        with self.assertRaisesRegex(ValueError, "WM_CLASS"):
            self.check(wm_class="omni-store.py OmniStore")

    def test_missing_process_rejected(self):
        with self.assertRaisesRegex(ValueError, "no live GNOME Mines"):
            self.check(output="org.gnome.Mines 99999\n")

    def test_wrong_process_rejected(self):
        (self.proc / "comm").write_text("python3\n")
        (self.proc / "cmdline").write_bytes(b"/usr/bin/python3\0omni-store.py\0")
        with self.assertRaisesRegex(ValueError, "no live GNOME Mines"):
            self.check()

    def test_other_flatpak_rejected(self):
        with self.assertRaisesRegex(ValueError, "no live GNOME Mines"):
            self.check(output="org.gnome.Calculator 4321\n")

    def test_flatpak_failure_rejected(self):
        with self.assertRaisesRegex(ValueError, "flatpak ps failed"):
            self.check(returncode=1)

    def test_bad_pid_rejected(self):
        with self.assertRaisesRegex(ValueError, "no live GNOME Mines"):
            self.check(output="org.gnome.Mines invalid\n")


if __name__ == "__main__":
    unittest.main()
