import unittest
from recovery_g2.boot_state import BootState, stage, select_boot, confirm, rollback

class BootModelTests(unittest.TestCase):
    def test_default_boot(self):
        self.assertEqual(select_boot(BootState()), ("A", BootState()))

    def test_three_attempts_then_fallback(self):
        state = stage(BootState(), "B")
        for expected in (2, 1, 0):
            slot, state = select_boot(state)
            self.assertEqual(slot, "B")
            self.assertEqual(state.attempts_left, expected)
        slot, state = select_boot(state)
        self.assertEqual(slot, "A")
        self.assertIsNone(state.candidate)

    def test_last_attempt_can_be_confirmed(self):
        state = stage(BootState(), "B", attempts=1)
        slot, state = select_boot(state)
        self.assertEqual(confirm(state, slot, True).confirmed, "B")

    def test_unhealthy_not_confirmed(self):
        state = stage(BootState(), "B")
        with self.assertRaises(ValueError):
            confirm(state, "B", False)
        with self.assertRaises(ValueError):
            confirm(state, "A", True)

    def test_active_slot_cannot_be_staged(self):
        with self.assertRaises(ValueError):
            stage(BootState(), "A")

    def test_pending_update_cannot_be_overwritten(self):
        with self.assertRaises(ValueError):
            stage(stage(BootState(), "B"), "B")

    def test_invalid_state_rejected(self):
        for kwargs in ({"confirmed": "C"}, {"candidate": "A"}, {"attempts_left": 2},
                       {"generation": -1}, {"candidate": "B", "attempts_left": -1}):
            with self.assertRaises(ValueError):
                BootState(**kwargs)

    def test_explicit_rollback(self):
        state = rollback(stage(BootState(), "B"))
        self.assertEqual((state.confirmed, state.candidate), ("A", None))

if __name__ == "__main__":
    unittest.main()
