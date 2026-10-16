"""Integration smoke test: Horizon panel and launcher coexist in one X session."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

horizon = load("horizon_integration_launcher", "image/includes/opt/nexus/horizon.py")
panel = load("horizon_integration_panel", "image/includes/opt/nexus/horizon-panel.py")

class DesktopIntegrationSmoke(unittest.TestCase):
    def test_panel_launcher_and_search_share_display(self):
        top = panel.HorizonPanel()
        launcher = horizon.Horizon()
        try:
            top.update()
            launcher.update()
            self.assertTrue(top.winfo_exists())
            self.assertTrue(launcher.winfo_exists())
            self.assertNotEqual(top.attributes("-topmost"), 1)
            self.assertTrue(top.clock.get())
            launcher.search.set("Nexus Agent")
            launcher.update()
            self.assertEqual(len(launcher.list_frame.winfo_children()), 1)
            with patch.object(horizon, "launch") as start:
                launcher.launch_first()
            start.assert_called_once_with(("x-terminal-emulator", "-e", "/usr/local/bin/nexus-agent"))
        finally:
            launcher.destroy()
            top.destroy()

if __name__ == "__main__":
    unittest.main()
