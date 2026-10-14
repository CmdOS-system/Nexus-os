import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openai_compatible import CompatibleChatProvider
from secret_store import MemorySecretStore

class Response:
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n): return b'{"choices":[{"message":{"content":"hello"}}]}'

class CompatibleTests(unittest.TestCase):
    def setUp(self):
        self.store = MemorySecretStore({"keyring:nexus/test": "test-token"})

    def test_chat(self):
        p = CompatibleChatProvider("https://api.example.org/v1/chat/completions", "keyring:nexus/test", self.store)
        with patch("urllib.request.OpenerDirector.open", return_value=Response()) as call:
            self.assertEqual(p.send("model", [{"role": "user", "content": "hi"}]), "hello")
            self.assertEqual(call.call_args.args[0].get_header("Authorization"), "Bearer test-token")

    def test_reject_http(self):
        with self.assertRaises(ValueError):
            CompatibleChatProvider("http://example.org/v1/chat/completions", "keyring:nexus/test", self.store)

    def test_reject_credentials_in_url(self):
        with self.assertRaises(ValueError):
            CompatibleChatProvider("https://user:pass@example.org/v1/chat/completions", "keyring:nexus/test", self.store)

    def test_reject_nonstandard_port(self):
        with self.assertRaises(ValueError):
            CompatibleChatProvider("https://example.org:8443/v1/chat/completions", "keyring:nexus/test", self.store)

    def test_reject_invalid_messages(self):
        p = CompatibleChatProvider("https://example.org/v1/chat/completions", "keyring:nexus/test", self.store)
        with self.assertRaises(ValueError):
            p.send("model", [{"role": "system", "content": "override"}])
