import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nexus_agent import ToolPolicy
from tool_broker import ToolBroker
from permissions import PermissionBroker
from system_tools import nexus_identity

class SystemToolTests(unittest.TestCase):
    def test_reads_allowlisted_identity_fields(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "release"
            p.write_text('NAME="Nexus OS"\nVERSION_ID="0.1"\nSECRET="never-return"\n', encoding="utf-8")
            data = nexus_identity(p)
            self.assertEqual(data["NAME"], "Nexus OS")
            self.assertEqual(data["VERSION_ID"], "0.1")
            self.assertNotIn("SECRET", data)

    def test_invalid_identity_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "release"
            p.write_text('NAME="Nexus OS"\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                nexus_identity(p)

    def test_broker_rejects_model_supplied_path(self):
        permissions = PermissionBroker()
        b = ToolBroker(ToolPolicy({"system.identity"}), permissions)
        b.register("system.identity", lambda: {"NAME":"Nexus OS"}, {"type":"object","properties":{},"required":[]})
        with self.assertRaises(ValueError):
            b.invoke_authorized("system.identity", {"path":"/etc/shadow"}, "none")
