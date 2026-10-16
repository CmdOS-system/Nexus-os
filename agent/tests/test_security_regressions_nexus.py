"""Security regressions for BYOAI and file grants (stdlib unittest)."""
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from settings import AISettings
from file_grants import FileGrantStore


class SecurityRegressions(unittest.TestCase):
    def test_cloud_consent_must_be_boolean(self):
        for consent in (1, "true", "false", [], None):
            with self.subTest(consent=consent), self.assertRaises(ValueError):
                AISettings(mode="cloud", provider="example", model="test", cloud_consent=consent).validate()
        AISettings(mode="cloud", provider="example", model="test", cloud_consent=True).validate()

    def test_file_swap_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "selected.txt"
            path.write_text("approved")
            store = FileGrantStore()
            token = store.grant(path)
            replacement = Path(directory) / "replacement.txt"
            replacement.write_text("replacement")
            replacement.replace(path)
            with self.assertRaises(PermissionError):
                store.consume_text(token)

    def test_symlink_swap_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "selected.txt"
            other = Path(directory) / "other.txt"
            path.write_text("approved")
            other.write_text("secret")
            store = FileGrantStore()
            token = store.grant(path)
            path.unlink()
            path.symlink_to(other)
            with self.assertRaises(PermissionError):
                store.consume_text(token)

    def test_read_limit_and_one_use(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "selected.txt"
            path.write_text("hello")
            store = FileGrantStore()
            token = store.grant(path)
            with self.assertRaises(ValueError):
                store.consume_text(token, max_bytes=4)
            with self.assertRaises(PermissionError):
                store.consume_text(token)


if __name__ == "__main__":
    unittest.main()
