import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from providers import AIProvider
from session import AgentSession

class FakeProvider(AIProvider):
    def __init__(self, answers=None, error=None):
        self.answers = list(answers or [])
        self.error = error
        self.calls = []

    def send(self, model, messages):
        self.calls.append((model, messages))
        if self.error:
            raise self.error
        return self.answers.pop(0)

class SessionTests(unittest.TestCase):
    def test_context_sent_as_roles(self):
        p = FakeProvider(["First answer", "Second answer"])
        s = AgentSession(p, "test")
        self.assertEqual(s.ask("First question"), "First answer")
        s.ask("Follow up")
        messages = p.calls[-1][1]
        self.assertEqual(messages[0], {"role": "user", "content": "First question"})
        self.assertEqual(messages[1], {"role": "assistant", "content": "First answer"})
        self.assertEqual(messages[2], {"role": "user", "content": "Follow up"})

    def test_failure_does_not_change_history(self):
        s = AgentSession(FakeProvider(error=RuntimeError("offline")), "test")
        with self.assertRaises(RuntimeError):
            s.ask("hello")
        self.assertEqual(s.history.snapshot(), [])

    def test_clear(self):
        s = AgentSession(FakeProvider(["answer"]), "test")
        s.ask("hello")
        s.clear()
        self.assertEqual(s.history.snapshot(), [])

    def test_reject_non_adapter(self):
        with self.assertRaises(TypeError):
            AgentSession(object(), "model")

    def test_empty_prompt(self):
        with self.assertRaises(ValueError):
            AgentSession(FakeProvider(["unused"]), "test").ask("  ")

    def test_invalid_provider_response_does_not_change_history(self):
        s = AgentSession(FakeProvider([""]), "test")
        with self.assertRaises(ValueError):
            s.ask("hello")
        self.assertEqual(s.history.snapshot(), [])
