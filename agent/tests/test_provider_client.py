import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nexus_agent import Provider
from provider_client import chat

class FakeResponse:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n): return b'{"message":{"content":"Hello from local AI"}}'

class ClientTests(unittest.TestCase):
    def test_local_chat(self):
        with patch("urllib.request.OpenerDirector.open", return_value=FakeResponse()):
            self.assertEqual(chat(Provider("ollama", "http://127.0.0.1:11434", True), "example-model", "Hi"), "Hello from local AI")

    def test_reject_cloud_without_credentials_layer(self):
        with self.assertRaises(ValueError):
            chat(Provider("cloud", "https://example.org"), "model", "Hi")

    def test_reject_empty_message(self):
        with self.assertRaises(ValueError):
            chat(Provider("ollama", "http://localhost:11434", True), "model", "")

if __name__ == "__main__":
    unittest.main()
