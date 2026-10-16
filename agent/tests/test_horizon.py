"""Behavior tests for the Nexus Horizon application launcher."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2] / "image/includes/opt/nexus/horizon.py"
spec = importlib.util.spec_from_file_location("nexus_horizon", SOURCE)
horizon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(horizon)

class HorizonTests(unittest.TestCase):
    def test_search_matches_name_and_description(self):
        self.assertEqual(horizon.matching_apps("control")[0][0], "Nexus Control Center")
        self.assertEqual(horizon.matching_apps("installation plan")[0][0], "Installation Preview")
        self.assertEqual(horizon.matching_apps("AI assistant")[0][0], "Nexus Agent")
        self.assertEqual(horizon.matching_apps("not-a-real-application"), [])

    def test_commands_are_fixed_argv_not_shell(self):
        with patch.object(horizon.subprocess, "Popen") as popen:
            horizon.launch(("thunar",))
        popen.assert_called_once_with(("thunar",), stdin=horizon.subprocess.DEVNULL, close_fds=True)
        for _, _, argv in horizon.APPLICATIONS:
            self.assertIsInstance(argv, tuple)
            self.assertNotIn("sh", argv[:1])
            self.assertNotIn("bash", argv[:1])

if __name__ == "__main__":
    unittest.main()
