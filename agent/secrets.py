"""Secret resolution boundary. No plaintext persistence is implemented."""
from abc import ABC, abstractmethod

class SecretStore(ABC):
    @abstractmethod
    def resolve(self, reference: str) -> str:
        raise NotImplementedError

class MemorySecretStore(SecretStore):
    """Test/development store. Values exist only in process memory."""
    def __init__(self, values=None):
        self._values = dict(values or {})

    def resolve(self, reference: str) -> str:
        if not isinstance(reference, str) or not reference.startswith("keyring:"):
            raise ValueError("Invalid secret reference")
        try:
            value = self._values[reference]
        except KeyError:
            raise KeyError("Secret reference not found") from None
        if not isinstance(value, str) or not value:
            raise ValueError("Resolved secret is invalid")
        return value
