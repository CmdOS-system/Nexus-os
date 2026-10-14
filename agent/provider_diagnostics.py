"""Minimal provider connectivity diagnostic with secret-safe errors."""
from providers import AIProvider

def test_provider_connection(adapter: AIProvider, model: str) -> tuple[bool,str]:
    if not isinstance(adapter,AIProvider):
        raise TypeError("Adapter must implement AIProvider")
    if not isinstance(model,str) or not model.strip():
        raise ValueError("Model is required")
    try:
        answer=adapter.send(model,[{"role":"user","content":"Reply with OK."}])
    except Exception as exc:
        # Never surface provider exception text: HTTP libraries may include sensitive context.
        return False, type(exc).__name__
    if not isinstance(answer,str) or not answer.strip():
        return False,"EmptyResponse"
    return True,"Connected"
