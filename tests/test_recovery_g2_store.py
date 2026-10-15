import tempfile
import unittest
from recovery_g2.boot_state import BootState, stage
from recovery_g2.store import RedundantStore, RecoveryRequired

class StoreTests(unittest.TestCase):
    def test_roundtrip_and_single_copy_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RedundantStore(directory)
            store.save(BootState())
            state = stage(store.load(), "B")
            store.save(state)
            store.paths[0].write_bytes(b"corrupt")
            self.assertEqual(store.load(), state)

    def test_both_copies_corrupt(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RedundantStore(directory)
            store.save(BootState())
            for path in store.paths:
                path.write_bytes(b"broken")
            with self.assertRaises(RecoveryRequired):
                store.load()

    def test_stale_generation_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RedundantStore(directory)
            store.save(BootState())
            with self.assertRaises(ValueError):
                store.save(BootState())


    def test_same_generation_conflict_fails_closed(self):
        from recovery_g2.store import encode
        with tempfile.TemporaryDirectory() as directory:
            store = RedundantStore(directory)
            store.paths[0].write_bytes(encode(BootState(confirmed="A", generation=4)))
            store.paths[1].write_bytes(encode(BootState(confirmed="B", generation=4)))
            with self.assertRaises(RecoveryRequired):
                store.load()

    def test_recovery_after_torn_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            store = RedundantStore(directory)
            store.save(BootState())
            store.paths[1].write_bytes(b'{"payload":')
            self.assertEqual(store.load(), BootState())

    def test_missing_metadata_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(RecoveryRequired):
                RedundantStore(directory).load()
