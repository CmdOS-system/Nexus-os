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

    def test_installer_launches_with_fixed_interpreter_and_path(self):
        with patch.object(module.Path, "is_file", return_value=True), \
             patch.object(module.subprocess, "Popen") as spawn:
            self.app._open_installer_preview()
        args, kwargs = spawn.call_args
        self.assertEqual(args[0], ["/usr/bin/python3", "/opt/nexus/installer-preview.py"])
        self.assertIs(kwargs["stdin"], module.subprocess.DEVNULL)
        self.assertTrue(kwargs["close_fds"])

    def test_local_probe_reports_model_availability(self):
        self.app.mode.set("local")
        self.app.provider.set("ollama")
        self.app.model.set("llama3")
        with patch.object(module, "check_local_model", return_value=(True, "Local model is installed.")) as probe, \
             patch.object(module.threading, "Thread") as thread:
            self.app._check_local_model()
            callback = thread.call_args.kwargs["target"]
            with patch.object(self.app, "after", side_effect=lambda delay, fn: fn()):
                callback()
            probe.assert_called_once_with("llama3")
        self.assertIn("Ready:", self.app.probe_result.get())

    def test_missing_installer_does_not_spawn_process(self):
        with patch.object(module.Path, "is_file", return_value=False), \
             patch.object(module.subprocess, "Popen") as spawn, \
             patch.object(module.messagebox, "showerror") as error:
            self.app._open_installer_preview()
        spawn.assert_not_called()
        error.assert_called_once()

if __name__ == "__main__":
    unittest.main()
