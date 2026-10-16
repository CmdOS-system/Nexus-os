"""Read-only Ollama model availability probe; loopback only, no prompts or credentials."""
import json
from urllib.request import urlopen
from urllib.error import URLError

OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"

def check_local_model(model: str, *, timeout: float = 2.0) -> tuple[bool, str]:
    """Return availability without invoking inference or revealing network errors."""
    if not isinstance(model, str) or not model.strip():
        return False, "Choose a local model first."
    if not isinstance(timeout, (int, float)) or not 0 < timeout <= 10:
        raise ValueError("Invalid probe timeout")
    try:
        with urlopen(OLLAMA_TAGS_URL, timeout=timeout) as response:
            if response.status != 200:
                return False, "Local model service is not ready."
            payload = response.read(1024 * 1024 + 1)
        if len(payload) > 1024 * 1024:
            return False, "Local model list exceeds safe size."
        data = json.loads(payload)
        models = data.get("models") if isinstance(data, dict) else None
        if not isinstance(models, list):
            return False, "Local model service returned invalid data."
        names = {item.get("name") for item in models if isinstance(item, dict) and isinstance(item.get("name"), str)}
        selected = model.strip()
        if selected in names or (":" not in selected and selected + ":latest" in names):
            return True, "Local model is installed and the service responded."
        return False, "Local service responded, but the selected model is not installed."
    except (OSError, URLError, ValueError, UnicodeError, TimeoutError):
        return False, "Local model service is unavailable or returned invalid data."
