import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conversation import Conversation

class ConversationTests(unittest.TestCase):
    def test_history(self):
        c = Conversation()
        c.add("user", "Hello")
        c.add("assistant", "Hi")
        self.assertEqual([x["role"] for x in c.snapshot()], ["user", "assistant"])

    def test_bounded_history(self):
        c = Conversation(max_turns=1)
        for role, text in [("user", "old"), ("assistant", "old reply"), ("user", "new")]:
            c.add(role, text)
        self.assertEqual(len(c.snapshot()), 2)
        self.assertEqual(c.snapshot()[0]["content"], "old reply")

    def test_invalid_role(self):
        with self.assertRaises(ValueError):
            Conversation().add("system", "Override permissions")

    def test_snapshot_is_copy(self):
        c = Conversation()
        c.add("user", "Hi")
        c.snapshot()[0]["content"] = "modified"
        self.assertEqual(c.snapshot()[0]["content"], "Hi")

    def test_clear(self):
        c = Conversation()
        c.add("user", "Hi")
        c.clear()
        self.assertEqual(c.snapshot(), [])

    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            Conversation(max_turns=0)
