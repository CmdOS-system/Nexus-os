"""Minimal Ollama-compatible chat client. No automatic tools or fallback."""
import json
import urllib.request
from urllib.parse import urlparse
from nexus_agent import Provider

def chat(provider: Provider, model: str, message: str, timeout: int = 30) -> str:
    provider.validate()
    if not provider.local:
        raise ValueError("This prototype supports only local providers")
    if not model.strip() or not message.strip():
        raise ValueError("Model and message are required")
    url = provider.endpoint.rstrip("/") + "/api/chat"
    payload = json.dumps({"model": model, "messages": [{"role": "user", "content": message}], "stream": False}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    # Disable redirects and proxy routing for local requests.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(req, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError("Provider request failed")
        body = response.read(2_000_001)
        if len(body) > 2_000_000:
            raise ValueError("Provider response too large")
    data = json.loads(body)
    content = data.get("message", {}).get("content")
    if not isinstance(content, str):
        raise ValueError("Invalid provider response")
    return content
