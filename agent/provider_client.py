"""Local Ollama chat client with native role-separated message history."""
import json
import urllib.request
from nexus_agent import Provider

def chat_messages(provider: Provider, model: str, messages: list, timeout: int = 30) -> str:
    provider.validate()
    if not provider.local:
        raise ValueError("This prototype supports only local providers")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("Model is required")
    if not isinstance(messages, list) or not messages:
        raise ValueError("Messages are required")
    for item in messages:
        if not isinstance(item, dict) or set(item) != {"role", "content"}:
            raise ValueError("Invalid message structure")
        if item["role"] not in ("user", "assistant") or not isinstance(item["content"], str) or not item["content"].strip():
            raise ValueError("Invalid message")
    url = provider.endpoint.rstrip("/") + "/api/chat"
    payload = json.dumps({"model": model, "messages": messages, "stream": False}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
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

def chat(provider: Provider, model: str, message: str, timeout: int = 30) -> str:
    if not isinstance(message, str) or not message.strip():
        raise ValueError("Message is required")
    return chat_messages(provider, model, [{"role": "user", "content": message}], timeout)
