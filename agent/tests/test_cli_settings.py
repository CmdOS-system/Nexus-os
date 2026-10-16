"""Regression tests for saved local model selection in the Nexus Agent CLI."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agent"))
from cli import resolve_local_model
from settings import AISettings
from settings_store import save_settings


class LocalModelSelectionTests(unittest.TestCase):
    def test_saved_ollama_model_is_used(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ai-settings.json"
            save_settings(path, AISettings("local", "ollama", "llama3", False))
            self.assertEqual(resolve_local_model(settings_path=path), "llama3")

    def test_disabled_ai_cannot_start_local_chat(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.json"
            with self.assertRaises(ValueError):
                resolve_local_model(settings_path=path)

    def test_cloud_settings_are_not_used_by_local_chat(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ai-settings.json"
            save_settings(path, AISettings("cloud", "remote", "model", True))
            with self.assertRaises(ValueError):
                resolve_local_model(settings_path=path)

    def test_non_ollama_local_provider_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ai-settings.json"
            save_settings(path, AISettings("local", "other", "model", False))
            with self.assertRaises(ValueError):
                resolve_local_model(settings_path=path)

    def test_corrupt_settings_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ai-settings.json"
            path.write_text('{"mode": "local"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                resolve_local_model(settings_path=path)

    def test_hybrid_settings_do_not_enable_local_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ai-settings.json"
            save_settings(path, AISettings("hybrid", "ollama", "model", True))
            with self.assertRaises(ValueError):
                resolve_local_model(settings_path=path)

    def test_explicit_model_override(self):
        self.assertEqual(resolve_local_model("test-model"), "test-model")


if __name__ == "__main__":
    unittest.main()
