"""Regression tests for PID-less GNOME Mines X11 evidence validation."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "nexus_evidence_validator", Path(__file__).with_name("validate-evidence.py"))
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class MinesWindowTests(unittest.TestCase):
    def test_recognizes_app_class_without_a_window_pid(self):
        self.assertTrue(validator.linux_mines_window_identity(
            "org.gnome.Mines org.gnome.Mines", "Mines"))
        self.assertTrue(validator.linux_mines_window_identity(
            "gnome-mines Gnome-mines", ""))

    def test_recognizes_mines_title(self):
        self.assertTrue(validator.linux_mines_window_identity("", "GNOME Mines"))

    def test_rejects_store_identity(self):
        self.assertFalse(validator.linux_mines_window_identity(
            "omni-store.py OmniStore", "Nexus OmniStore"))

    def test_finds_real_process_directly_in_proc(self):
        with tempfile.TemporaryDirectory() as root:
            proc = Path(root) / "4321"
            proc.mkdir()
            (proc / "comm").write_text("gnome-mines\n")
            (proc / "cmdline").write_bytes(b"/app/bin/gnome-mines\0")
            self.assertEqual(validator.linux_mines_proc_owner(Path(root)), 4321)

    def test_ignores_unrelated_processes(self):
        with tempfile.TemporaryDirectory() as root:
            proc = Path(root) / "4321"
            proc.mkdir()
            (proc / "comm").write_text("python3\n")
            (proc / "cmdline").write_bytes(b"python3\0omni-store.py\0")
            self.assertEqual(validator.linux_mines_proc_owner(Path(root)), 0)


if __name__ == "__main__":
    unittest.main()
