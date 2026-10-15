import unittest
from recovery_g2.bls import entry_status, after_boot_attempt, bless_entry

class BootAssessmentTests(unittest.TestCase):
    def test_failed_three_attempts(self):
        name = "nexus-B+3.conf"
        self.assertEqual(entry_status(name), "indeterminate")
        for expected in ("nexus-B+2-1.conf", "nexus-B+1-2.conf",
                         "nexus-B+0-3.conf"):
            name = after_boot_attempt(name)
            self.assertEqual(name, expected)
        self.assertEqual(entry_status(name), "bad")
        with self.assertRaises(ValueError):
            after_boot_attempt(name)

    def test_success_after_second_attempt(self):
        name = after_boot_attempt("nexus-B+3.conf")
        name = after_boot_attempt(name)
        self.assertEqual(bless_entry(name), "nexus-B.conf")
        self.assertEqual(entry_status("nexus-B.conf"), "good")

    def test_clean_entry_cannot_be_decremented(self):
        with self.assertRaises(ValueError):
            after_boot_attempt("nexus-A.conf")
        with self.assertRaises(ValueError):
            bless_entry("nexus-A.conf")
