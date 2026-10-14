# BYOAI configuration

Nexus OS separates provider configuration from credentials.

Provider configuration may contain:
- provider name and adapter kind;
- whether the provider is enabled;
- whether it is local;
- model identifiers;
- a secret reference such as `keyring:nexus/provider`.

Provider configuration must never contain the secret value itself.

## Secret boundary

The current prototype validates references only. A later SecretStore implementation will resolve those references through the desktop keyring or another OS-backed credential service. The resolved credential must be scoped to the provider request and must not be copied into logs, conversation history, crash reports, or model prompts.

## Local AI

Local providers such as Ollama do not need a cloud credential reference. Local inference remains a first-class mode so Nexus Agent can operate without requiring an external AI subscription.
