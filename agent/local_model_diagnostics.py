"""Read-only Ollama model availability probe; loopback only, no prompts or credentials."""
import json
from urllib.request import build_opener, HTTPRedirectHandler, ProxyHandler
from urllib.error import URLError, HTTPError

OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"

class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def _open_local_tags(timeout):
    # Do not follow a malicious local service redirect to the public internet.
    opener = build_opener(ProxyHandler({}), _NoRedirect)
    return opener.open(OLLAMA_TAGS_URL, timeout=timeout)

def check_local_model(model: str, *, timeout: float = 2.0) -> tuple[bool, str]:
    """Return availability without invoking inference or revealing network errors."""
    if not isinstance(model, str) or not model.strip():
        return False, "Choose a local model first."
    if not isinstance(timeout, (int, float)) or not 0 < timeout <= 10:
        raise ValueError("Invalid probe timeout")
    try:
        with _open_local_tags(timeout) as response:
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
