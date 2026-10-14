# Nexus Agent AI routing policy

Nexus Agent must not silently send user content to a different AI provider.

## Rules

1. The user chooses which providers are enabled.
2. Local processing is preferred when it satisfies the requested capability.
3. Cloud fallback requires an enabled provider and explicit user policy.
4. Credentials are never stored in conversation history or provider configuration files.
5. A model capability is descriptive, never an authorization grant.
6. Tool execution remains governed by ToolPolicy even when a model supports tool calling.
7. Provider switching must be visible to the user.
8. Sensitive context must not be forwarded between providers by default.

## Capability vocabulary

Initial capabilities: chat, tools, vision, json, streaming.

This vocabulary is intentionally small. Unsupported or unknown capabilities fail validation rather than silently enabling behavior.

## Future routing

A later router may select among user-enabled providers based on required capabilities, local/cloud preference, availability, latency, and cost. It must never treat model output as authorization and must preserve the user's privacy choices.
