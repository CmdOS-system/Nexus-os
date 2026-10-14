import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nexus_agent import Provider
from session import AgentSession

class SessionTests(unittest.TestCase):
    def setUp(self):
        self.session = AgentSession(Provider("ollama", "http://127.0.0.1:11434", True), "test")

    def test_context_sent_on_second_turn(self):
        with patch("session.chat", side_effect=["First answer", "Second answer"]) as mocked:
            self.assertEqual(self.session.ask("First question"), "First answer")
            self.session.ask("Follow up")
            self.assertIn("assistant: First answer", mocked.call_args.args[2])
            self.assertIn("user: Follow up", mocked.call_args.args[2])

    def test_failure_does_not_change_history(self):
        with patch("session.chat", side_effect=RuntimeError("offline")):
            with self.assertRaises(RuntimeError):
                self.session.ask("hello")
        self.assertEqual(self.session.history.snapshot(), [])

    def test_clear(self):
        with patch("session.chat", return_value="answer"):
            self.session.ask("hello")
        self.session.clear()
        self.assertEqual(self.session.history.snapshot(), [])

    def test_reject_cloud(self):
        with self.assertRaises(ValueError):
            AgentSession(Provider("cloud", "https://example.org"), "model")

    def test_empty_prompt(self):
        with self.assertRaises(ValueError):
            self.session.ask("  ")
