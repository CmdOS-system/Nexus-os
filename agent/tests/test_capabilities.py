import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from capabilities import Capabilities

class CapabilityTests(unittest.TestCase):
    def test_supports_required_features(self):
        c = Capabilities.of("chat", "vision")
        self.assertTrue(c.supports("chat"))
        self.assertTrue(c.supports("chat", "vision"))
        self.assertFalse(c.supports("tools"))

    def test_unknown_capability_rejected(self):
        with self.assertRaises(ValueError):
            Capabilities.of("shell")

    def test_empty_capabilities_are_valid(self):
        self.assertFalse(Capabilities.of().supports("chat"))
