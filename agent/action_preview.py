"""Pure, non-executing Nexus Flow action preview primitives."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from permissions import PermissionBroker, PermissionRequest

RISK_EXPLANATIONS = {
    "R0": "Read-only action; no user data should be changed.",
    "R1": "Local change; review the result and available undo path.",
    "R2": "Consequential change; review affected resources and grant explicit permission.",
    "R3": "Privileged or destructive change; independent confirmation is required.",
}


@dataclass(frozen=True)
class ActionPreview:
    request: PermissionRequest
    description: str
    risk_explanation: str
    affected_resources: tuple[str, ...]
    requires_independent_confirmation: bool


def prepare_action_preview(
    broker: PermissionBroker, *, tool: str, arguments: dict,
    description: str, risk: str, affected_resources: tuple[str, ...],
) -> ActionPreview:
    """Register a permission request without invoking a tool or granting access."""
    if not isinstance(broker, PermissionBroker):
        raise TypeError("PermissionBroker required")
    if risk not in RISK_EXPLANATIONS:
        raise ValueError("Unknown risk class")
    if not isinstance(description, str) or not description.strip():
        raise ValueError("Nonempty description required")
    if not isinstance(affected_resources, tuple) or any(
        not isinstance(x, str) or not x.strip() for x in affected_resources
    ):
        raise ValueError("Affected resources must be a tuple of nonempty strings")
    if risk != "R0" and not affected_resources:
        raise ValueError("Changes require explicit affected resources")
    request = broker.request(tool, arguments, description, risk)
    return ActionPreview(
        request=request, description=description,
        risk_explanation=RISK_EXPLANATIONS[risk],
        affected_resources=affected_resources,
        requires_independent_confirmation=(risk == "R3"),
    )
