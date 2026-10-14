"""Conversation-aware local session using native chat roles."""
from conversation import Conversation
from nexus_agent import Provider
from provider_client import chat_messages

class AgentSession:
    def __init__(self, provider: Provider, model: str, max_turns: int = 12):
        self.provider = provider.validate()
        if not self.provider.local:
            raise ValueError("Only local models supported by this prototype")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("A model is required")
        self.model = model
        self.history = Conversation(max_turns=max_turns)

    def ask(self, prompt: str) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("A prompt is required")
        messages = self.history.snapshot()
        messages.append(dict(role="user", content=prompt))
        response = chat_messages(self.provider, self.model, messages)
        self.history.add("user", prompt)
        self.history.add("assistant", response)
        return response

    def clear(self):
        self.history.clear()
