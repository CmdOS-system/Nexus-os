# Nexus Agent Tool Broker

The Tool Broker is the authorization boundary between AI output and operating-system actions.

Version 1 is intentionally non-privileged and contains no shell executor. Tools must be registered by trusted Nexus code with a fixed name, handler and argument schema. A model cannot dynamically register a new tool.

Every invocation is checked against ToolPolicy and requires explicit approval. Arguments are fail-closed: undeclared fields, missing required fields and basic type mismatches are rejected before the handler runs.

Provider capability and tool authorization are separate concepts. A model that supports tool calling still has zero operating-system authority until Nexus policy and the user authorize a specific registered operation.

Future work: typed nested schemas, risk classes, one-shot consent tokens, audit events, portal-mediated file selection, polkit mediation for narrowly defined privileged services, cancellation and prompt-injection defenses.
