"""Xvfb smoke coverage for the actual Nexus Control Center Tk window."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agent"))
SOURCE = ROOT / "image/includes/opt/nexus/control-center.py"
spec = importlib.util.spec_from_file_location("nexus_control_center", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ControlCenterSmoke(unittest.TestCase):
    def setUp(self):
        with patch.object(module, "load_settings", return_value=module.AISettings()):
            self.app = module.App()
        self.app.update_idletasks()

    def tearDown(self):
        self.app.destroy()

    def test_mode_guidance_is_not_a_connection_claim(self):
        self.app.mode.set("cloud")
        self.assertIn("connection not verified", self.app.status.get())
        self.app.mode.set("local")
        self.assertIn("not verified", self.app.status.get())

    def test_nonlocal_probe_never_calls_network(self):
        self.app.mode.set("cloud")
        self.app.provider.set("ollama")
        with patch.object(module, "check_local_model") as probe:
            self.app._check_local_model()
            probe.assert_not_called()
        self.assertIn("Select Local mode", self.app.probe_result.get())

    def test_missing_installer_does_not_spawn_process(self):
        with patch.object(module.Path, "is_file", return_value=False), \
             patch.object(module.subprocess, "Popen") as spawn, \
             patch.object(module.messagebox, "showerror") as error:
            self.app._open_installer_preview()
        spawn.assert_not_called()
        error.assert_called_once()

if __name__ == "__main__":
    unittest.main()
