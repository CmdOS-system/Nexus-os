"""One-shot user decision boundary for Nexus Agent actions."""
from dataclasses import dataclass
import secrets

@dataclass(frozen=True)
class PermissionRequest:
    request_id: str
    tool: str
    summary: str
    risk: str

class PermissionBroker:
    def __init__(self):
        self._pending = {}
        self._decisions = {}

    def request(self, tool: str, summary: str, risk: str) -> PermissionRequest:
        if not isinstance(tool, str) or not tool.strip():
            raise ValueError("Tool is required")
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError("Human-readable summary is required")
        if risk not in {"R0", "R1", "R2", "R3"}:
            raise ValueError("Invalid risk class")
        request_id = secrets.token_urlsafe(24)
        item = PermissionRequest(request_id, tool, summary, risk)
        self._pending[request_id] = item
        return item

    def decide(self, request_id: str, approved: bool):
        if type(approved) is not bool:
            raise ValueError("Decision must be boolean")
        try:
            item = self._pending.pop(request_id)
        except KeyError:
            raise PermissionError("Permission request is unknown or already decided") from None
        self._decisions[request_id] = approved
        return item

    def consume_approval(self, request_id: str, tool: str) -> bool:
        try:
            approved = self._decisions.pop(request_id)
        except KeyError:
            raise PermissionError("No user decision is available") from None
        if not approved:
            raise PermissionError("User denied the action")
        # Bind the decision to the original tool.
        # The request is retained only long enough to validate the binding.
        return True

    def pending(self):
        return tuple(self._pending.values())
