import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nexus_agent import ToolPolicy
from permissions import PermissionBroker
from tool_broker import ToolBroker

SCHEMA={"type":"object","properties":{"text":{"type":"string"}},"required":["text"]}

class BrokerTests(unittest.TestCase):
    def make(self):
        p=PermissionBroker()
        b=ToolBroker(ToolPolicy({"echo"}), p)
        b.register("echo", lambda text:text, SCHEMA)
        return b,p

    def approve(self,p,args):
        r=p.request("echo", args, "Echo approved text", "R0")
        p.decide(r.request_id, True)
        return r.request_id

    def test_bound_approval_executes(self):
        b,p=self.make(); args={"text":"hello"}
        self.assertEqual(b.invoke_authorized("echo",args,self.approve(p,args)),"hello")

    def test_missing_permission_broker_blocks(self):
        b=ToolBroker(ToolPolicy({"echo"}))
        b.register("echo",lambda text:text,SCHEMA)
        with self.assertRaises(PermissionError):
            b.invoke_authorized("echo",{"text":"hello"},"none")

    def test_changed_arguments_block(self):
        b,p=self.make(); rid=self.approve(p,{"text":"hello"})
        with self.assertRaises(PermissionError):
            b.invoke_authorized("echo",{"text":"changed"},rid)

    def test_unexpected_argument_rejected(self):
        b,p=self.make()
        with self.assertRaises(ValueError):
            b.invoke_authorized("echo",{"text":"hello","command":"rm"},"none")

    def test_duplicate_registration_rejected(self):
        b,p=self.make()
        with self.assertRaises(ValueError):
            b.register("echo",lambda text:text,SCHEMA)
