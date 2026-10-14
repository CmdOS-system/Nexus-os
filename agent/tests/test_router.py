import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from capabilities import Capabilities
from providers import AIProvider
from router import AIRouter

class Dummy(AIProvider):
    def send(self, model, messages):
        return "ok"

class RouterTests(unittest.TestCase):
    def test_prefers_local(self):
        r = AIRouter()
        r.add("cloud", Dummy(), Capabilities.of("chat"), False)
        r.add("local", Dummy(), Capabilities.of("chat"), True)
        self.assertEqual(r.select().name, "local")

    def test_cloud_requires_permission(self):
        r = AIRouter()
        r.add("cloud", Dummy(), Capabilities.of("chat"), False)
        with self.assertRaises(LookupError):
            r.select()
        self.assertEqual(r.select(allow_cloud=True).name, "cloud")

    def test_capability_filter(self):
        r = AIRouter()
        r.add("text", Dummy(), Capabilities.of("chat"), True)
        r.add("vision", Dummy(), Capabilities.of("chat", "vision"), True)
        self.assertEqual(r.select(("chat", "vision")).name, "vision")

    def test_no_matching_provider(self):
        r = AIRouter()
        r.add("text", Dummy(), Capabilities.of("chat"), True)
        with self.assertRaises(LookupError):
            r.select(("tools",))
