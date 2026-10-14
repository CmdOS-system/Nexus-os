import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nexus_agent import Provider, ToolPolicy

class ProviderTests(unittest.TestCase):
    def test_local_loopback(self):
        self.assertIsNotNone(Provider("ollama", "http://127.0.0.1:11434", True).validate())

    def test_cloud_https(self):
        self.assertIsNotNone(Provider("cloud", "https://api.example.org/v1").validate())

    def test_reject_insecure_remote(self):
        with self.assertRaises(ValueError):
            Provider("remote", "http://example.org").validate()

    def test_reject_non_loopback_local(self):
        with self.assertRaises(ValueError):
            Provider("local", "https://example.org", True).validate()

    def test_reject_embedded_credentials(self):
        with self.assertRaises(ValueError):
            Provider("remote", "https://secret:token@example.org").validate()

class PolicyTests(unittest.TestCase):
    def test_deny_by_default(self):
        with self.assertRaises(PermissionError):
            ToolPolicy().authorize("read_file", True)

    def test_approval_required(self):
        with self.assertRaises(PermissionError):
            ToolPolicy({"read_file"}).authorize("read_file")

    def test_allow_approved(self):
        self.assertTrue(ToolPolicy({"read_file"}).authorize("read_file", True))

if __name__ == "__main__":
    unittest.main()
