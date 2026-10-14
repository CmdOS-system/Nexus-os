import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from file_grants import FileGrantStore, register_file_tools
from nexus_agent import ToolPolicy
from permissions import PermissionBroker
from tool_broker import ToolBroker

class FileGrantTests(unittest.TestCase):
    def test_one_shot_read(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"note.txt"; p.write_text("hello",encoding="utf-8")
            s=FileGrantStore(); token=s.grant(p.resolve())
            self.assertEqual(s.consume_text(token),"hello")
            with self.assertRaises(PermissionError): s.consume_text(token)

    def test_relative_path_rejected(self):
        with self.assertRaises(ValueError): FileGrantStore().grant(Path("note.txt"))

    def test_directory_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): FileGrantStore().grant(Path(d).resolve())

    def test_broker_reads_only_granted_file(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"note.txt"; p.write_text("approved text",encoding="utf-8")
            grants=FileGrantStore(); token=grants.grant(p.resolve())
            permissions=PermissionBroker()
            broker=ToolBroker(ToolPolicy({"file.read_text"}),permissions)
            register_file_tools(broker,grants)
            args={"grant_token":token}
            req=permissions.request("file.read_text",args,"Read selected file","R1")
            permissions.decide(req.request_id,True)
            self.assertEqual(broker.invoke_authorized("file.read_text",args,req.request_id),"approved text")

    def test_path_injection_rejected_before_execution(self):
        grants=FileGrantStore(); permissions=PermissionBroker()
        broker=ToolBroker(ToolPolicy({"file.read_text"}),permissions)
        register_file_tools(broker,grants)
        with self.assertRaises(ValueError):
            broker.invoke_authorized("file.read_text",{"grant_token":"opaque","path":"/etc/shadow"},"none")
