"""Privacy-first provider selection for Nexus Agent."""
from dataclasses import dataclass
from capabilities import Capabilities
from providers import AIProvider

@dataclass(frozen=True)
class Route:
    name: str
    provider: AIProvider
    capabilities: Capabilities
    local: bool

class AIRouter:
    def __init__(self):
        self._routes = []

    def add(self, name, provider, capabilities, local):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Route name is required")
        if not isinstance(provider, AIProvider):
            raise TypeError("provider must implement AIProvider")
        if not isinstance(capabilities, Capabilities):
            raise TypeError("capabilities must be Capabilities")
        self._routes.append(Route(name, provider, capabilities, bool(local)))

    def select(self, required=("chat",), allow_cloud=False):
        matches = [r for r in self._routes if r.capabilities.supports(*required)]
        local = [r for r in matches if r.local]
        if local:
            return local[0]
        if allow_cloud:
            cloud = [r for r in matches if not r.local]
            if cloud:
                return cloud[0]
        raise LookupError("No authorized provider satisfies the requested capabilities")
