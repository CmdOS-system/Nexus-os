"""Provider/model capability declarations for safe routing."""
from dataclasses import dataclass

_ALLOWED = frozenset({"chat", "tools", "vision", "json", "streaming"})

@dataclass(frozen=True)
class Capabilities:
    values: frozenset

    def __post_init__(self):
        unknown = self.values - _ALLOWED
        if unknown:
            raise ValueError("Unknown capabilities")

    @classmethod
    def of(cls, *values):
        return cls(frozenset(values))

    def supports(self, *required):
        return set(required).issubset(self.values)
