import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from secret_store import MemorySecretStore

class SecretStoreTests(unittest.TestCase):
    def test_resolve(self):
        s = MemorySecretStore({"keyring:nexus/test": "token"})
        self.assertEqual(s.resolve("keyring:nexus/test"), "token")

    def test_missing_reference(self):
        with self.assertRaises(KeyError):
            MemorySecretStore().resolve("keyring:nexus/missing")

    def test_reject_plain_value_as_reference(self):
        with self.assertRaises(ValueError):
            MemorySecretStore().resolve("plain-token")

    def test_reject_empty_secret(self):
        with self.assertRaises(ValueError):
            MemorySecretStore({"keyring:nexus/test": ""}).resolve("keyring:nexus/test")
