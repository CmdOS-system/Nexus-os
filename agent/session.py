"""Provider-independent conversation session."""
from conversation import Conversation
from providers import AIProvider

class AgentSession:
    def __init__(self, provider: AIProvider, model: str, max_turns: int = 12):
        if not isinstance(provider, AIProvider):
            raise TypeError("provider must implement AIProvider")
        if not isinstance(model, str) or not model.strip():
            raise ValueError("A model is required")
        self.provider = provider
        self.model = model
        self.history = Conversation(max_turns=max_turns)

    def ask(self, prompt: str) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("A prompt is required")
        messages = self.history.snapshot()
        messages.append(dict(role="user", content=prompt))
        response = self.provider.send(self.model, messages)
        if not isinstance(response, str) or not response.strip():
            raise ValueError("Provider returned an invalid response")
        self.history.add("user", prompt)
        self.history.add("assistant", response)
        return response

    def clear(self):
        self.history.clear()
