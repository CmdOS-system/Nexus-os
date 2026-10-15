import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from nexus_recovery_metadata import Metadata, atomic_write, decode, encode, load


class RecoveryMetadataTests(unittest.TestCase):
    def sample(self, **overrides):
        values = dict(generation=7, good="A", candidate="B", state="pending_boot",
                      attempts_left=3, transaction_id=42)
        values.update(overrides)
        return Metadata(**values)

    def test_round_trip(self):
        m = self.sample()
        self.assertEqual(decode(encode(m)), m)

    def test_corruption_is_detected(self):
        raw = bytearray(encode(self.sample()))
        i = raw.index(b'"generation":7') + len(b'"generation":')
        raw[i] = ord("8")
        with self.assertRaises(ValueError):
            decode(bytes(raw))

    def test_truncated_metadata_is_rejected(self):
        raw = encode(self.sample())
        with self.assertRaises(ValueError):
            decode(raw[: len(raw)//2])

    def test_invalid_slot_is_rejected(self):
        with self.assertRaises(ValueError):
            encode(self.sample(good="C"))

    def test_candidate_cannot_equal_good(self):
        with self.assertRaises(ValueError):
            encode(self.sample(candidate="A"))

    def test_negative_attempts_are_rejected(self):
        with self.assertRaises(ValueError):
            encode(self.sample(attempts_left=-1))

    def test_atomic_replace_loads_new_complete_generation(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "state.json")
            first = self.sample(generation=1, transaction_id=1)
            second = self.sample(generation=2, transaction_id=2)
            atomic_write(p, first)
            self.assertEqual(load(p), first)
            atomic_write(p, second)
            self.assertEqual(load(p), second)
            self.assertEqual([x for x in os.listdir(d) if x.startswith(".nexus-recovery-")], [])

    def test_existing_state_survives_failed_encode_before_replace(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "state.json")
            good = self.sample(generation=3)
            atomic_write(p, good)
            with self.assertRaises(ValueError):
                atomic_write(p, self.sample(good="C"))
            self.assertEqual(load(p), good)


if __name__ == "__main__":
    unittest.main()
