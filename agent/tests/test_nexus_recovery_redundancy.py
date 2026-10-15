import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import nexus_recovery_metadata as storage
from nexus_recovery_metadata import Metadata, atomic_write, load_redundant, write_redundant


class RecoveryRedundancyTests(unittest.TestCase):
    def meta(self, tx, generation=None):
        return Metadata(generation=tx if generation is None else generation,
                        good="A", candidate="B", state="pending_boot",
                        attempts_left=3, transaction_id=tx)

    def test_newest_valid_transaction_wins(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a"), os.path.join(d, "b")
            atomic_write(a, self.meta(1))
            atomic_write(b, self.meta(2))
            self.assertEqual(load_redundant(a, b), self.meta(2))

    def test_corrupt_primary_falls_back_to_secondary(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a"), os.path.join(d, "b")
            write_redundant(a, b, self.meta(4))
            with open(a, "wb") as f:
                f.write(b"corrupt")
            self.assertEqual(load_redundant(a, b), self.meta(4))

    def test_both_invalid_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a"), os.path.join(d, "b")
            for p in (a, b):
                with open(p, "wb") as f:
                    f.write(b"bad")
            with self.assertRaises(ValueError):
                load_redundant(a, b)

    def test_conflicting_same_transaction_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a"), os.path.join(d, "b")
            atomic_write(a, self.meta(8, generation=8))
            atomic_write(b, self.meta(8, generation=9))
            with self.assertRaises(ValueError):
                load_redundant(a, b)

    def test_failure_updating_primary_keeps_new_secondary(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a"), os.path.join(d, "b")
            write_redundant(a, b, self.meta(1))
            real = storage.atomic_write
            calls = {"n": 0}
            def fail_second(path, meta):
                calls["n"] += 1
                if calls["n"] == 2:
                    raise OSError("simulated crash before primary commit")
                return real(path, meta)
            with patch.object(storage, "atomic_write", side_effect=fail_second):
                with self.assertRaises(OSError):
                    write_redundant(a, b, self.meta(2))
            self.assertEqual(load_redundant(a, b), self.meta(2))

    def test_same_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "state")
            with self.assertRaises(ValueError):
                write_redundant(p, p, self.meta(1))


if __name__ == "__main__":
    unittest.main()
