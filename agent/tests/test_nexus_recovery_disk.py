import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from nexus_recovery_disk import DISK_SIZE, SLOT_SIZE, create_disk, read_slot, write_slot


class RecoveryDiskTests(unittest.TestCase):
    def disk(self, d):
        p = os.path.join(d, "disk.img")
        create_disk(p)
        return p

    def test_create_exact_disposable_disk(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.disk(d)
            self.assertEqual(os.path.getsize(p), DISK_SIZE)

    def test_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.disk(d)
            with self.assertRaises(ValueError):
                create_disk(p)

    def test_slot_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.disk(d)
            write_slot(p, "A", b"known-good")
            self.assertEqual(read_slot(p, "A"), b"known-good")

    def test_updating_inactive_slot_preserves_good_slot_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.disk(d)
            write_slot(p, "A", b"known-good")
            before = open(p, "rb").read(SLOT_SIZE)
            write_slot(p, "B", b"candidate")
            after = open(p, "rb").read(SLOT_SIZE)
            self.assertEqual(before, after)
            self.assertEqual(read_slot(p, "A"), b"known-good")
            self.assertEqual(read_slot(p, "B"), b"candidate")

    def test_oversized_payload_cannot_cross_slot_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.disk(d)
            with self.assertRaises(ValueError):
                write_slot(p, "B", b"x" * SLOT_SIZE)

    def test_corruption_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.disk(d)
            write_slot(p, "A", b"known-good")
            with open(p, "r+b") as f:
                f.seek(100)
                f.write(b"X")
            with self.assertRaises(ValueError):
                read_slot(p, "A")

    def test_wrong_sized_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "wrong.img")
            open(p, "wb").write(b"x")
            with self.assertRaises(ValueError):
                write_slot(p, "A", b"payload")

    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = self.disk(d)
            link = os.path.join(d, "link.img")
            os.symlink(p, link)
            with self.assertRaises(ValueError):
                read_slot(link, "A")


if __name__ == "__main__":
    unittest.main()
