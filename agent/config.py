"""Safe BYOAI configuration model. Secret values are never accepted here."""
from dataclasses import dataclass, field
import re

_KEYRING_PREFIX="keyring:nexus/"
_SAFE_PROVIDER=re.compile(r"^[A-Za-z0-9._-]{1,64}$")

def provider_secret_ref(provider: str) -> str:
    if not isinstance(provider,str) or not _SAFE_PROVIDER.fullmatch(provider):
        raise ValueError("Provider identifier must use letters, numbers, dot, dash or underscore")
    return _KEYRING_PREFIX + provider

@dataclass(frozen=True)
class ProviderConfig:
    name: str
    kind: str
    enabled: bool = True
    local: bool = False
    secret_ref: str | None = None
    models: tuple = field(default_factory=tuple)

    def validate(self):
        if not isinstance(self.name,str) or not self.name.strip() or not isinstance(self.kind,str) or not self.kind.strip():
            raise ValueError("Provider name and kind are required")
        if self.local and self.secret_ref:
            raise ValueError("Local provider must not require a cloud secret reference")
        if self.secret_ref is not None:
            expected=provider_secret_ref(self.name)
            if self.secret_ref != expected:
                raise ValueError("Secret reference must match the Nexus provider keyring namespace")
        for model in self.models:
            if not isinstance(model,str) or not model.strip():
                raise ValueError("Invalid model name")
        return self
