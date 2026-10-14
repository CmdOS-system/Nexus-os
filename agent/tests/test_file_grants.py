import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from file_grants import FileGrantStore

class FileGrantTests(unittest.TestCase):
    def test_one_shot_read(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "note.txt"
            p.write_text("hello", encoding="utf-8")
            s = FileGrantStore()
            token = s.grant(p.resolve())
            self.assertEqual(s.consume_text(token), "hello")
            with self.assertRaises(PermissionError):
                s.consume_text(token)

    def test_relative_path_rejected(self):
        with self.assertRaises(ValueError):
            FileGrantStore().grant(Path("note.txt"))

    def test_directory_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                FileGrantStore().grant(Path(d).resolve())

    def test_size_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "large.txt"
            p.write_text("12345", encoding="utf-8")
            s = FileGrantStore()
            token = s.grant(p.resolve())
            with self.assertRaises(ValueError):
                s.consume_text(token, max_bytes=4)

    def test_unknown_token_rejected(self):
        with self.assertRaises(PermissionError):
            FileGrantStore().consume_text("not-a-grant")
