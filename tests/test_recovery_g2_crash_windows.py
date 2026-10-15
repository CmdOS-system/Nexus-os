"""Crash-window and recovery invariants for redundant metadata."""
import json
import tempfile
import unittest
from recovery_g2.boot_state import BootState, stage, rollback
from recovery_g2.store import RedundantStore, encode, RecoveryRequired

class CrashWindowTests(unittest.TestCase):
    def test_newest_valid_generation_wins_after_interrupted_write(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RedundantStore(directory)
            store.save(BootState())
            staged = stage(store.load(), "B")
            store.paths[0].write_bytes(encode(staged))
            self.assertEqual(store.load(), staged)
            recovered = rollback(store.load())
            store.save(recovered)
            self.assertEqual(store._copies(), [recovered, recovered])

    def test_checksum_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RedundantStore(directory)
            store.save(BootState())
            for path in store.paths:
                record = json.loads(path.read_bytes())
                record["payload"]["generation"] = 9
                path.write_bytes(json.dumps(record).encode())
            with self.assertRaises(RecoveryRequired):
                store.load()

    def test_candidate_exhausted_still_recoverable(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RedundantStore(directory)
            store.save(BootState())
            exhausted = BootState(confirmed="A", candidate="B",
                                  attempts_left=0, generation=1)
            store.save(exhausted)
            self.assertEqual(store.load(), exhausted)
