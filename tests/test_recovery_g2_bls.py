import unittest
from recovery_g2.bls import parse_entry, tentative_entry

class BootEntryTests(unittest.TestCase):
    def test_clean_entry(self):
        self.assertEqual(parse_entry("nexus-A.conf"),
                         {"name": "nexus-A", "tries_left": None, "tries_done": None})

    def test_counted_entry(self):
        self.assertEqual(parse_entry("nexus-B+2-1.conf"),
                         {"name": "nexus-B", "tries_left": 2, "tries_done": 1})

    def test_new_tentative_entry(self):
        self.assertEqual(tentative_entry("nexus-B", 3), "nexus-B+3.conf")

    def test_rejects_traversal_and_bad_budgets(self):
        for filename in ("../nexus.conf", "/nexus.conf", "nexus/evil.conf",
                         "nexus.conf/../../bad.conf", "nexus+1.efi"):
            with self.assertRaises(ValueError):
                parse_entry(filename)
        for tries in (True, 0, 11):
            with self.assertRaises(ValueError):
                tentative_entry("nexus-B", tries)
