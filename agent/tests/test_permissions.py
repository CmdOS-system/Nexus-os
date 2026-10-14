import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from permissions import PermissionBroker

ARGS = {"grant_token": "abc"}

class PermissionTests(unittest.TestCase):
    def test_request_is_pending(self):
        b = PermissionBroker()
        r = b.request("file.read_text", ARGS, "Read selected file", "R1")
        self.assertEqual(b.pending(), (r,))

    def test_decision_is_one_shot(self):
        b = PermissionBroker()
        r = b.request("file.read_text", ARGS, "Read selected file", "R1")
        b.decide(r.request_id, True)
        self.assertTrue(b.consume_approval(r.request_id, "file.read_text", ARGS))
        with self.assertRaises(PermissionError):
            b.consume_approval(r.request_id, "file.read_text", ARGS)

    def test_changed_arguments_are_rejected(self):
        b = PermissionBroker()
        r = b.request("file.read_text", ARGS, "Read selected file", "R1")
        b.decide(r.request_id, True)
        with self.assertRaises(PermissionError):
            b.consume_approval(r.request_id, "file.read_text", {"grant_token":"changed"})

    def test_changed_tool_is_rejected(self):
        b = PermissionBroker()
        r = b.request("file.read_text", ARGS, "Read selected file", "R1")
        b.decide(r.request_id, True)
        with self.assertRaises(PermissionError):
            b.consume_approval(r.request_id, "system.identity", ARGS)

    def test_denial_blocks(self):
        b = PermissionBroker()
        r = b.request("file.read_text", ARGS, "Read selected file", "R1")
        b.decide(r.request_id, False)
        with self.assertRaises(PermissionError):
            b.consume_approval(r.request_id, "file.read_text", ARGS)

    def test_invalid_risk_rejected(self):
        with self.assertRaises(ValueError):
            PermissionBroker().request("shell", {}, "Run anything", "R4")
