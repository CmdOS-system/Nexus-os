import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "includes/opt/nexus"))
from omni_store_sources import SourceStore, validate_source


class SourceValidationTests(unittest.TestCase):
    def test_normalizes_secure_store_urls(self):
        result = validate_source("  Example   Store ", " HTTPS://Store.Example/apps?channel=stable#top ")
        self.assertEqual(result["name"], "Example Store")
        self.assertEqual(result["url"], "https://store.example/apps?channel=stable")

    def test_rejects_insecure_or_executable_schemes(self):
        for url in ("http://store.example", "javascript:alert(1)", "file:///tmp/apps", "store.example", "https://bad host.example"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_source("Store", url)

    def test_rejects_embedded_credentials_and_malformed_ports(self):
        for url in ("https://user:secret@store.example", "https://store.example:nope/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_source("Store", url)

    def test_add_duplicate_remove_and_private_file_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config" / "nexus" / "stores.json"
            store = SourceStore(path)
            first = store.add("Trusted Store", "https://store.example/catalog")
            self.assertEqual(store.list()[0]["id"], first["id"])
            with self.assertRaisesRegex(ValueError, "ya está registrada"):
                store.add("Duplicate", "https://STORE.example/catalog")
            if os.name == "posix":
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
            self.assertTrue(store.remove(first["id"]))
            self.assertEqual(store.list(), [])

    def test_ignores_corrupt_registry_without_crashing(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "stores.json"
            path.write_text("{not-json", encoding="utf-8")
            self.assertEqual(SourceStore(path).list(), [])


if __name__ == "__main__":
    unittest.main()
