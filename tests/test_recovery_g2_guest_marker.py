import unittest

from recovery_g2.guest_marker import (
    SUCCESS_EXIT_CODE, SUCCESS_GUEST_VALUE, classify_guest_exit,
)


class GuestMarkerTests(unittest.TestCase):
    def test_qemu_exit_code_matches_device_formula(self):
        self.assertEqual(SUCCESS_GUEST_VALUE, 42)
        self.assertEqual(SUCCESS_EXIT_CODE, 85)

    def test_only_exact_guest_marker_counts_as_success(self):
        self.assertTrue(classify_guest_exit(85)["guest_marker_seen"])
        for value in (0, 1, 2, 84, 86, 137, -9):
            with self.subTest(value=value):
                self.assertFalse(classify_guest_exit(value)["guest_marker_seen"])

    def test_timeout_never_confirms_guest(self):
        self.assertEqual(classify_guest_exit(None, timed_out=True)["status"],
                         "inconclusive_timeout")

    def test_invalid_return_code_rejected(self):
        for value in (None, True, "85"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    classify_guest_exit(value)
