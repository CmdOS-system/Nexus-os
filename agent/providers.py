"""Provider adapter contracts for Nexus Agent."""
from abc import ABC, abstractmethod
from provider_client import chat_messages

class AIProvider(ABC):
    @abstractmethod
    def send(self, model: str, messages: list) -> str:
        raise NotImplementedError

class OllamaProvider(AIProvider):
    def __init__(self, provider):
        self.provider = provider.validate()
        if not self.provider.local:
            raise ValueError("Ollama adapter requires a local provider")

    def send(self, model: str, messages: list) -> str:
        return chat_messages(self.provider, model, messages)

class ProviderRegistry:
    def __init__(self):
        self._providers = {}

    def register(self, name: str, adapter: AIProvider):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Provider name is required")
        if not isinstance(adapter, AIProvider):
            raise TypeError("Adapter must implement AIProvider")
        self._providers[name] = adapter

    def get(self, name: str) -> AIProvider:
        try:
            return self._providers[name]
        except KeyError:
            raise KeyError("Provider is not registered") from None

    def names(self):
        return tuple(sorted(self._providers))
