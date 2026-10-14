"""Privacy-first provider selection for Nexus Agent."""
from dataclasses import dataclass
from capabilities import Capabilities
from providers import AIProvider
from settings import AISettings

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

    def select_for_settings(self, settings: AISettings, required=("chat",)):
        settings.validate()
        if settings.mode == "off":
            raise LookupError("AI is disabled")

        matches = [
            r for r in self._routes
            if r.name == settings.provider and r.capabilities.supports(*required)
        ]
        if settings.mode == "local":
            matches = [r for r in matches if r.local]
        elif settings.mode == "cloud":
            matches = [r for r in matches if not r.local]
        elif settings.mode == "hybrid":
            local = [r for r in matches if r.local]
            if local:
                return local[0]
            matches = [r for r in matches if not r.local]

        if matches:
            return matches[0]
        raise LookupError("Configured provider is not authorized for this AI mode")
