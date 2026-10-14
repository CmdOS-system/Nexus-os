# Nexus Agent tool risk model

Nexus tools are grouped by the effect they can have, not by what the model calls them.

- R0: fixed-source, non-sensitive system metadata. Example: Nexus OS identity.
- R1: user-selected read access through an explicit chooser/portal.
- R2: user-data mutation with a preview and one-shot approval.
- R3: system configuration or package operations mediated by a narrowly scoped privileged service and OS authorization.
- R4: prohibited generic authority, including unrestricted root shell or arbitrary privileged command execution.

The current implementation begins at R0. Even R0 tools remain allowlisted and approval-gated by ToolPolicy. A model cannot turn a fixed-source metadata tool into arbitrary filesystem access by supplying a path.

Risk level is independent of whether the provider is local or cloud. Cloud models do not receive extra authority, and local models are not implicitly trusted.
