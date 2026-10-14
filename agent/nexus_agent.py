"""Nexus Agent: provider registry and fail-closed tool authorization prototype."""
from dataclasses import dataclass
from urllib.parse import urlparse

@dataclass(frozen=True)
class Provider:
    name: str
    endpoint: str
    local: bool = False

    def validate(self):
        parsed = urlparse(self.endpoint)
        if parsed.username or parsed.password or parsed.fragment:
            raise ValueError("Credentials and fragments are not allowed in endpoints")
        if parsed.scheme not in ("https", "http") or not parsed.hostname:
            raise ValueError("Invalid provider endpoint")
        if parsed.scheme == "http" and (not self.local or parsed.hostname not in ("localhost", "127.0.0.1", "::1")):
            raise ValueError("Plain HTTP allowed only for explicit loopback providers")
        if self.local and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError("Local providers must use loopback")
        return self

class ToolPolicy:
    """Explicit authorization is required for every tool, including read operations."""
    def __init__(self, allowed=None):
        self.allowed = frozenset(allowed or ())

    def authorize(self, tool, approved=False):
        if not isinstance(tool, str) or tool not in self.allowed:
            raise PermissionError("Tool not on allowlist")
        if not approved:
            raise PermissionError("Explicit approval required")
        return True
