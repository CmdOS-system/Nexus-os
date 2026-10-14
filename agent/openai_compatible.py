"""Explicit HTTPS-only chat-completions adapter (no system tools)."""
import json
import urllib.request
from urllib.parse import urlsplit
from providers import AIProvider
from secrets import SecretStore

class CompatibleChatProvider(AIProvider):
    def __init__(self, endpoint: str, secret_ref: str, secret_store: SecretStore, timeout: int = 30):
        parsed = urlsplit(endpoint)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment or parsed.query:
            raise ValueError("Cloud endpoint must be an HTTPS URL without credentials, query or fragment")
        if parsed.port is not None and parsed.port != 443:
            raise ValueError("Cloud endpoint must use HTTPS port 443")
        if not isinstance(secret_ref, str) or not secret_ref.startswith("keyring:"):
            raise ValueError("Keyring reference required")
        if not isinstance(secret_store, SecretStore):
            raise TypeError("SecretStore required")
        if type(timeout) is not int or not 1 <= timeout <= 120:
            raise ValueError("Invalid timeout")
        self.endpoint = endpoint.rstrip("/")
        self.secret_ref = secret_ref
        self.secret_store = secret_store
        self.timeout = timeout

    def send(self, model: str, messages: list) -> str:
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Model required")
        if not isinstance(messages, list) or not messages:
            raise ValueError("Messages required")
        for msg in messages:
            if not isinstance(msg, dict) or set(msg) != {"role", "content"} or msg["role"] not in ("user", "assistant") or not isinstance(msg["content"], str) or not msg["content"].strip():
                raise ValueError("Invalid message")
        token = self.secret_store.resolve(self.secret_ref)
        payload = json.dumps({"model": model, "messages": messages, "stream": False}).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=payload, headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"}, method="POST")
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        opener = urllib.request.build_opener(NoRedirect())
        with opener.open(req, timeout=self.timeout) as response:
            body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise ValueError("Provider response too large")
        result = json.loads(body)
        choices = result.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("Invalid provider response")
        answer = choices[0].get("message", {}).get("content")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Invalid provider response")
        return answer
