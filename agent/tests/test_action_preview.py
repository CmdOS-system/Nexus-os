import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from action_preview import prepare_action_preview
from permissions import PermissionBroker


class ActionPreviewTests(unittest.TestCase):
    def test_read_only_preview_does_not_approve(self):
        broker = PermissionBroker()
        preview = prepare_action_preview(
            broker, tool="search_files", arguments={"query": "report"},
            description="Search selected files", risk="R0", affected_resources=(),
        )
        self.assertEqual(preview.request.risk, "R0")
        self.assertEqual(len(broker.pending()), 1)
        with self.assertRaises(PermissionError):
            broker.consume_approval(preview.request.request_id, "search_files", {"query": "report"})

    def test_mutating_preview_requires_affected_resources(self):
        broker = PermissionBroker()
        with self.assertRaises(ValueError):
            prepare_action_preview(
                broker, tool="delete_file", arguments={"path": "/tmp/a"},
                description="Delete file", risk="R2", affected_resources=(),
            )
        self.assertFalse(broker.pending())

    def test_destructive_action_requires_independent_confirmation(self):
        broker = PermissionBroker()
        preview = prepare_action_preview(
            broker, tool="erase_disk", arguments={"path": "/dev/vdb"},
            description="Erase disk", risk="R3", affected_resources=("/dev/vdb",),
        )
        self.assertTrue(preview.requires_independent_confirmation)
        self.assertEqual(preview.affected_resources, ("/dev/vdb",))

    def test_rejects_invalid_resource_types(self):
        with self.assertRaises(ValueError):
            prepare_action_preview(
                PermissionBroker(), tool="edit", arguments={},
                description="Edit", risk="R1", affected_resources=["/tmp/a"],
            )


if __name__ == "__main__":
    unittest.main()
