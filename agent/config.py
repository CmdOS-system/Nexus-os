"""Safe BYOAI configuration model. Secret values are never accepted here."""
from dataclasses import dataclass, field

@dataclass(frozen=True)
class ProviderConfig:
    name: str
    kind: str
    enabled: bool = True
    local: bool = False
    secret_ref: str | None = None
    models: tuple = field(default_factory=tuple)

    def validate(self):
        if not self.name.strip() or not self.kind.strip():
            raise ValueError("Provider name and kind are required")
        if self.local and self.secret_ref:
            raise ValueError("Local provider must not require a cloud secret reference")
        if self.secret_ref is not None:
            if not self.secret_ref.startswith("keyring:"):
                raise ValueError("Only keyring secret references are accepted")
            if len(self.secret_ref) <= len("keyring:"):
                raise ValueError("Secret reference is incomplete")
        for model in self.models:
            if not isinstance(model, str) or not model.strip():
                raise ValueError("Invalid model name")
        return self
