import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from permissions import PermissionBroker

class PermissionTests(unittest.TestCase):
    def test_request_is_pending(self):
        b = PermissionBroker()
        r = b.request("file.read_text", "Read selected file", "R1")
        self.assertEqual(b.pending(), (r,))

    def test_decision_is_one_shot(self):
        b = PermissionBroker()
        r = b.request("file.read_text", "Read selected file", "R1")
        b.decide(r.request_id, True)
        self.assertTrue(b.consume_approval(r.request_id, "file.read_text"))
        with self.assertRaises(PermissionError):
            b.consume_approval(r.request_id, "file.read_text")

    def test_denial_blocks(self):
        b = PermissionBroker()
        r = b.request("file.read_text", "Read selected file", "R1")
        b.decide(r.request_id, False)
        with self.assertRaises(PermissionError):
            b.consume_approval(r.request_id, "file.read_text")

    def test_cannot_decide_twice(self):
        b = PermissionBroker()
        r = b.request("system.identity", "Read Nexus version", "R0")
        b.decide(r.request_id, True)
        with self.assertRaises(PermissionError):
            b.decide(r.request_id, True)

    def test_invalid_risk_rejected(self):
        with self.assertRaises(ValueError):
            PermissionBroker().request("shell", "Run anything", "R4")
