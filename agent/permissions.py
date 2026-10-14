"""One-shot user decision boundary for Nexus Agent actions."""
from dataclasses import dataclass
import hashlib
import json
import uuid

def _arguments_digest(arguments: dict) -> str:
    if not isinstance(arguments, dict):
        raise ValueError("Arguments must be an object")
    try:
        normalized = json.dumps(arguments, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("Arguments must be JSON-compatible") from exc
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class PermissionRequest:
    request_id: str
    tool: str
    summary: str
    risk: str
    arguments_digest: str

class PermissionBroker:
    def __init__(self):
        self._pending = {}
        self._decisions = {}

    def request(self, tool: str, arguments: dict, summary: str, risk: str) -> PermissionRequest:
        if not isinstance(tool, str) or not tool.strip():
            raise ValueError("Tool is required")
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError("Human-readable summary is required")
        if risk not in {"R0", "R1", "R2", "R3"}:
            raise ValueError("Invalid risk class")
        item = PermissionRequest(
            uuid.uuid4().hex,
            tool,
            summary,
            risk,
            _arguments_digest(arguments),
        )
        self._pending[item.request_id] = item
        return item

    def decide(self, request_id: str, approved: bool):
        if type(approved) is not bool:
            raise ValueError("Decision must be boolean")
        try:
            item = self._pending.pop(request_id)
        except KeyError:
            raise PermissionError("Permission request is unknown or already decided") from None
        self._decisions[request_id] = (item, approved)
        return item

    def consume_approval(self, request_id: str, tool: str, arguments: dict) -> bool:
        try:
            item, approved = self._decisions.pop(request_id)
        except KeyError:
            raise PermissionError("No user decision is available") from None
        if item.tool != tool:
            raise PermissionError("Approval does not match requested tool")
        if item.arguments_digest != _arguments_digest(arguments):
            raise PermissionError("Approval does not match requested arguments")
        if not approved:
            raise PermissionError("User denied the action")
        return True

    def pending(self):
        return tuple(self._pending.values())
