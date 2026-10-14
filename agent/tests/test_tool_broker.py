import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nexus_agent import ToolPolicy
from tool_broker import ToolBroker

SCHEMA = {"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}

class BrokerTests(unittest.TestCase):
    def test_approved_allowlisted_tool(self):
        b = ToolBroker(ToolPolicy({"echo"}))
        b.register("echo", lambda text: text, SCHEMA)
        self.assertEqual(b.invoke("echo", {"text":"hello"}, approved=True), "hello")

    def test_requires_explicit_approval(self):
        b = ToolBroker(ToolPolicy({"echo"}))
        b.register("echo", lambda text: text, SCHEMA)
        with self.assertRaises(PermissionError):
            b.invoke("echo", {"text":"hello"})

    def test_rejects_unexpected_argument(self):
        b = ToolBroker(ToolPolicy({"echo"}))
        b.register("echo", lambda text: text, SCHEMA)
        with self.assertRaises(ValueError):
            b.invoke("echo", {"text":"hello","command":"rm"}, approved=True)

    def test_rejects_missing_argument(self):
        b = ToolBroker(ToolPolicy({"echo"}))
        b.register("echo", lambda text: text, SCHEMA)
        with self.assertRaises(ValueError):
            b.invoke("echo", {}, approved=True)

    def test_policy_checked_before_registration_lookup(self):
        b = ToolBroker(ToolPolicy())
        with self.assertRaises(PermissionError):
            b.invoke("unknown", {}, approved=True)

    def test_duplicate_registration_rejected(self):
        b = ToolBroker(ToolPolicy({"echo"}))
        b.register("echo", lambda text: text, SCHEMA)
        with self.assertRaises(ValueError):
            b.register("echo", lambda text: text, SCHEMA)
