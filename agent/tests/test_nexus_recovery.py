import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from nexus_recovery_sim import Phase, Recovery


class NexusRecoveryTests(unittest.TestCase):
    def prepared(self, **kwargs):
        r = Recovery(**kwargs)
        r.fetch()
        r.verify(True, True)
        r.stage()
        r.activate()
        return r

    def test_success_promotes_candidate_only_after_health(self):
        r = self.prepared()
        self.assertEqual(r.good, "A")
        self.assertEqual(r.boot(), "B")
        self.assertEqual(r.good, "A")
        r.health(True)
        self.assertEqual((r.good, r.candidate, r.phase), ("B", None, Phase.HEALTHY))

    def test_bad_signature_never_changes_good_slot(self):
        r = Recovery()
        r.fetch()
        r.verify(False, True)
        self.assertEqual((r.good, r.candidate, r.phase), ("A", None, Phase.IDLE))

    def test_bad_digest_never_changes_good_slot(self):
        r = Recovery()
        r.fetch()
        r.verify(True, False)
        self.assertEqual((r.good, r.candidate, r.phase), ("A", None, Phase.IDLE))

    def test_failed_candidate_rolls_back_after_bounded_attempts(self):
        r = self.prepared(max_attempts=3)
        for _ in range(3):
            self.assertEqual(r.boot(), "B")
            r.health(False)
        self.assertEqual((r.good, r.candidate, r.phase), ("A", None, Phase.IDLE))

    def test_unverified_payload_cannot_be_activated(self):
        r = Recovery()
        r.fetch()
        with self.assertRaises(ValueError):
            r.activate()
        self.assertEqual(r.good, "A")

    def test_candidate_cannot_be_confirmed_before_boot(self):
        r = self.prepared()
        with self.assertRaises(ValueError):
            r.health(True)
        self.assertEqual(r.good, "A")

    def test_next_generation_targets_previous_slot(self):
        r = self.prepared()
        r.boot()
        r.health(True)
        r.reset()
        r.fetch()
        self.assertEqual((r.good, r.candidate), ("B", "A"))

    def test_invalid_slot_is_rejected(self):
        with self.assertRaises(ValueError):
            Recovery(good="C")

    def test_zero_boot_attempt_policy_is_rejected(self):
        with self.assertRaises(ValueError):
            Recovery(max_attempts=0)


if __name__ == "__main__":
    unittest.main()
