"""Conversation-aware local Ollama session; tool execution deliberately unsupported."""
from conversation import Conversation
from nexus_agent import Provider
from provider_client import chat

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
        # Preserve previous context without altering state on failed calls.
        previous = self.history.snapshot()
        context = "\n".join(f"{m['role']}: {m['content']}" for m in previous)
        message = (context + "\nuser: " + prompt) if context else prompt
        response = chat(self.provider, self.model, message)
        self.history.add("user", prompt)
        self.history.add("assistant", response)
        return response

    def clear(self):
        self.history.clear()
