import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from capabilities import Capabilities
from providers import AIProvider
from router import AIRouter
from settings import AISettings

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

    def test_settings_off_blocks_all_routes(self):
        r = AIRouter()
        r.add("ollama", Dummy(), Capabilities.of("chat"), True)
        with self.assertRaises(LookupError):
            r.select_for_settings(AISettings())

    def test_local_settings_never_select_cloud(self):
        r = AIRouter()
        r.add("chosen", Dummy(), Capabilities.of("chat"), False)
        with self.assertRaises(LookupError):
            r.select_for_settings(AISettings("local", "chosen", "model"))

    def test_cloud_settings_select_only_cloud(self):
        r = AIRouter()
        r.add("chosen", Dummy(), Capabilities.of("chat"), True)
        with self.assertRaises(LookupError):
            r.select_for_settings(AISettings("cloud", "chosen", "model", True))

    def test_hybrid_prefers_local_matching_provider(self):
        r = AIRouter()
        r.add("chosen", Dummy(), Capabilities.of("chat"), False)
        r.add("chosen", Dummy(), Capabilities.of("chat"), True)
        route = r.select_for_settings(AISettings("hybrid", "chosen", "model", True))
        self.assertTrue(route.local)
