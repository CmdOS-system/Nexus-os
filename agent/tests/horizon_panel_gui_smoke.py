"""Smoke-test the optional Horizon panel on a real Tk virtual display."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2] / "image/includes/opt/nexus/horizon-panel.py"
spec = importlib.util.spec_from_file_location("nexus_horizon_panel", SOURCE)
panel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel)

class HorizonPanelSmoke(unittest.TestCase):
    def setUp(self):
        self.app = panel.HorizonPanel()
        self.app.update_idletasks()

    def tearDown(self):
        self.app.destroy()

    def test_clock_and_window(self):
        self.assertEqual(self.app.title(), "Nexus Horizon Panel")
        self.assertTrue(self.app.clock.get())
        self.assertEqual(self.app.winfo_height(), 48)
        self.assertNotEqual(self.app.attributes("-topmost"), 1)

    def test_launcher_command(self):
        with patch.object(panel, "start_launcher") as start:
            self.app.open_launcher()
        start.assert_called_once_with()

    def test_launcher_failure_is_reported(self):
        with patch.object(panel, "start_launcher", side_effect=FileNotFoundError), \
             patch("tkinter.messagebox.showerror") as error:
            self.app.open_launcher()
        error.assert_called_once()

if __name__ == "__main__":
    unittest.main()
