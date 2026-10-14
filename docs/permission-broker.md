# Nexus Permission Broker

PermissionBroker represents the user-decision boundary. AI output must never be able to manufacture an approved boolean and bypass the UI.

A trusted Nexus UI creates a permission request containing the tool name, a human-readable summary and the risk class. The user decision is recorded separately and consumed once.

R4 generic authority is intentionally not requestable.

This prototype is in-memory and is not yet wired into ToolBroker. Before production, approval must be cryptographically or structurally bound to the exact tool and normalized arguments, expiration must be enforced, concurrent-request behavior must be tested, and the UI must clearly show what data/action is being authorized.
