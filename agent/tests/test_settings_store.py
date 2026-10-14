import stat
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from settings import AISettings
from settings_store import load_settings, save_settings

class SettingsStoreTests(unittest.TestCase):
    def test_missing_file_defaults_to_off(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(load_settings(Path(d)/"missing.json"),AISettings())

    def test_round_trip_and_private_mode(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"nexus"/"ai-settings.json"
            expected=AISettings("local","ollama","model-a")
            save_settings(p,expected)
            self.assertEqual(load_settings(p),expected)
            self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o600)

    def test_invalid_settings_are_not_written(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"ai-settings.json"
            with self.assertRaises(ValueError):
                save_settings(p,AISettings("cloud","provider","model",False))
            self.assertFalse(p.exists())
