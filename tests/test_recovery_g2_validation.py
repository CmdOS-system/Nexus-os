"""Recovery G2 state invariants: malformed state must never select a boot slot."""
import unittest
from recovery_g2.boot_state import BootState, stage

class StateValidationTests(unittest.TestCase):
    def test_boolean_counters_rejected(self):
        for fields in ({"generation": True}, {"attempts_left": False}):
            with self.assertRaises(ValueError):
                BootState(**fields)

    def test_candidate_requires_attempt_budget_or_exhausted_state(self):
        self.assertEqual(BootState(candidate="B", attempts_left=0).candidate, "B")

    def test_stage_rejects_boolean_budget(self):
        with self.assertRaises(ValueError):
            stage(BootState(), "B", attempts=True)
