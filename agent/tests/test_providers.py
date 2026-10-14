import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nexus_agent import Provider
from providers import AIProvider, OllamaProvider, ProviderRegistry

class Dummy(AIProvider):
    def send(self, model, messages):
        return "ok"

class ProviderAdapterTests(unittest.TestCase):
    def test_registry(self):
        r = ProviderRegistry()
        r.register("dummy", Dummy())
        self.assertEqual(r.get("dummy").send("m", []), "ok")
        self.assertEqual(r.names(), ("dummy",))

    def test_unknown_provider(self):
        with self.assertRaises(KeyError):
            ProviderRegistry().get("missing")

    def test_ollama_requires_local(self):
        with self.assertRaises(ValueError):
            OllamaProvider(Provider("cloud", "https://example.org"))

    def test_ollama_send(self):
        adapter = OllamaProvider(Provider("ollama", "http://127.0.0.1:11434", True))
        with patch("providers.chat_messages", return_value="hello") as call:
            self.assertEqual(adapter.send("model", [{"role":"user","content":"hi"}]), "hello")
            call.assert_called_once()
