import unittest
from recovery_g2.simulator import simulate

class SimulatorTests(unittest.TestCase):
    def test_failed_candidate_falls_back(self):
        result = simulate(attempts=3)
        self.assertEqual([event["selected"] for event in result["events"]],
                         ["B", "B", "B", "A"])
        self.assertEqual(result["confirmed"], "A")
        self.assertIsNone(result["pending"])

    def test_candidate_confirmed_after_second_boot(self):
        result = simulate(attempts=3, healthy_on=2)
        self.assertEqual(result["confirmed"], "B")
        self.assertIsNone(result["pending"])
        self.assertEqual(result["events"][-1]["event"], "confirmed")

    def test_invalid_arguments_rejected(self):
        for kwargs in ({"attempts": 0}, {"attempts": 11},
                       {"attempts": 2, "healthy_on": 3}):
            with self.assertRaises(ValueError):
                simulate(**kwargs)
