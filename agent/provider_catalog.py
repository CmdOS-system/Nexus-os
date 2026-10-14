"""Built-in BYOAI provider metadata. Contains no credentials."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ProviderPreset:
    id: str
    label: str
    kind: str
    local: bool
    endpoint: str | None = None

_PRESETS=(
    ProviderPreset("ollama","Ollama (Local)","ollama",True,"http://127.0.0.1:11434"),
    ProviderPreset("openai-compatible","OpenAI-compatible HTTPS","compatible",False,None),
)

def presets():
    return _PRESETS

def get_preset(provider_id: str) -> ProviderPreset:
    for item in _PRESETS:
        if item.id == provider_id:
            return item
    raise KeyError("Unknown provider preset")
