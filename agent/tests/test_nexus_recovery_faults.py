"""Fault-injection tests for Nexus Recovery metadata (no disk devices)."""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import nexus_recovery_metadata as storage
from nexus_recovery_metadata import Metadata, atomic_write, load


class RecoveryFaultTests(unittest.TestCase):
    def sample(self, generation):
        return Metadata(generation=generation, good="A", candidate="B",
                        state="pending_boot", attempts_left=3,
                        transaction_id=generation)

    def test_replace_failure_preserves_last_good_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "state.json")
            atomic_write(path, self.sample(1))
            with patch.object(storage.os, "replace", side_effect=OSError("simulated power loss")):
                with self.assertRaises(OSError):
                    atomic_write(path, self.sample(2))
            self.assertEqual(load(path), self.sample(1))
            self.assertEqual(sorted(os.listdir(d)), ["state.json"])

    def test_file_fsync_failure_preserves_previous_generation(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "state.json")
            atomic_write(path, self.sample(1))
            with patch.object(storage.os, "fsync", side_effect=OSError("simulated fsync failure")):
                with self.assertRaises(OSError):
                    atomic_write(path, self.sample(2))
            self.assertEqual(load(path), self.sample(1))
            self.assertEqual(sorted(os.listdir(d)), ["state.json"])

    def test_corrupt_checksum_does_not_get_accepted(self):
        raw = storage.encode(self.sample(1))
        with self.assertRaises(ValueError):
            storage.decode(raw.replace(b'"generation":1', b'"generation":2'))

    def test_unsupported_schema_is_rejected(self):
        raw = storage.encode(self.sample(1))
        with self.assertRaises(ValueError):
            storage.decode(raw.replace(b'"schema":1', b'"schema":2'))

    def test_bad_utf8_is_rejected(self):
        with self.assertRaises(ValueError):
            storage.decode(b"\\xff")

    def test_repeated_atomic_writes_preserve_complete_records(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "state.json")
            for generation in range(1, 26):
                atomic_write(path, self.sample(generation))
                self.assertEqual(load(path), self.sample(generation))


if __name__ == "__main__":
    unittest.main()
