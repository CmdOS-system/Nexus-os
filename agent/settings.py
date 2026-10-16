"""Serializable Nexus AI preferences. Secrets are deliberately excluded."""
import json
from dataclasses import dataclass

_MODES = frozenset({"off", "local", "cloud", "hybrid"})

@dataclass(frozen=True)
class AISettings:
    mode: str = "off"
    provider: str | None = None
    model: str | None = None
    cloud_consent: bool = False

    def validate(self):
        if not isinstance(self.mode, str) or self.mode not in _MODES:
            raise ValueError("Invalid AI mode")
        if type(self.cloud_consent) is not bool:
            raise ValueError("Cloud consent must be a boolean")
        if self.mode == "off":
            if self.provider is not None or self.model is not None or self.cloud_consent:
                raise ValueError("Disabled AI must not carry provider state")
            return self
        if not isinstance(self.provider, str) or not self.provider.strip():
            raise ValueError("Provider is required")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("Model is required")
        if self.mode in ("cloud", "hybrid") and self.cloud_consent is not True:
            raise ValueError("Cloud use requires explicit consent")
        if self.mode == "local" and self.cloud_consent:
            raise ValueError("Local-only mode cannot enable cloud consent")
        return self

    def to_json(self) -> str:
        self.validate()
        return json.dumps({
            "mode": self.mode,
            "provider": self.provider,
            "model": self.model,
            "cloud_consent": self.cloud_consent,
        }, sort_keys=True)

    @classmethod
    def from_json(cls, raw: str):
        data = json.loads(raw)
        if not isinstance(data, dict) or set(data) != {"mode", "provider", "model", "cloud_consent"}:
            raise ValueError("Invalid settings document")
        return cls(**data).validate()
