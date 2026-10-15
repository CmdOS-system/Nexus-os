"""Integration checks for Recovery G2 boot state and durable metadata."""
import tempfile
import unittest
from recovery_g2.boot_state import BootState, stage, select_boot, confirm
from recovery_g2.store import RedundantStore

class RecoveryIntegrationTests(unittest.TestCase):
    def test_three_failed_boots_rollback_after_restarts(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RedundantStore(directory)
            store.save(BootState())
            store.save(stage(store.load(), "B"))
            for remaining in (2, 1, 0):
                slot, state = select_boot(RedundantStore(directory).load())
                self.assertEqual(slot, "B")
                self.assertEqual(state.attempts_left, remaining)
                RedundantStore(directory).save(state)
            slot, state = select_boot(RedundantStore(directory).load())
            self.assertEqual(slot, "A")
            store.save(state)
            self.assertEqual(RedundantStore(directory).load().confirmed, "A")
            self.assertIsNone(RedundantStore(directory).load().candidate)

    def test_healthy_candidate_commits_across_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RedundantStore(directory)
            store.save(BootState())
            store.save(stage(store.load(), "B", attempts=1))
            slot, pending = select_boot(RedundantStore(directory).load())
            store.save(pending)
            store.save(confirm(RedundantStore(directory).load(), slot, True))
            self.assertEqual(select_boot(RedundantStore(directory).load())[0], "B")

    def test_unconfirmed_last_attempt_falls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RedundantStore(directory)
            store.save(BootState())
            store.save(stage(store.load(), "B", attempts=1))
            _, pending = select_boot(store.load())
            store.save(pending)
            slot, rolled_back = select_boot(RedundantStore(directory).load())
            self.assertEqual(slot, "A")
            store.save(rolled_back)
            self.assertEqual(RedundantStore(directory).load().confirmed, "A")

if __name__ == "__main__":
    unittest.main()
