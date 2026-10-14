# Nexus Agent: Bring Your Own AI (BYOAI)

Status: design specification, not implemented.

## User promise
Users may select their preferred cloud or local AI provider, switch models, and optionally configure multiple models for distinct tasks. Nexus OS must remain usable without cloud AI.

## Interfaces
- ProviderAdapter: discoverModels, testConnection, infer, stream, supportsTools, capabilities.
- AgentOrchestrator: plans tasks, chooses provider by user policy, validates structured tool calls, tracks progress, and requests authorization.
- ToolBroker: enforces per-tool permissions, sandboxing, user confirmation, timeouts, and audit trails independent of the LLM.
- SecretStore: use OS keyring, never plaintext config or git.
- PrivacyGuard: redact secrets, preview outbound data, default local-only for sensitive tasks.

## Provider support roadmap
1. OpenAI-compatible HTTP adapters and Ollama localhost.
2. Native adapters for OpenAI, Anthropic Claude, Google Gemini.
3. Configurable compatible endpoints and enterprise gateways.
4. Optional LiteLLM gateway for routing/fallback; not required for basic installation.

## Configuration UI
Provider name, endpoint, model selector, connection test, default model, per-task override, local/cloud privacy notice, budget caps, fallback opt-in, and delete credentials.

## Security requirements
No shell access by default. Model responses are untrusted. Destructive or privileged operations need explicit confirmation, and privilege elevation occurs outside model control. Tool calls must be schema validated, rate limited, scoped, logged with redaction, and cancellable. Avoid sending private files to cloud without informed user approval. Protect against prompt injection and SSRF via custom endpoints.

## Acceptance tests
- Switch providers without changing agent tools.
- Operate with network disabled using a supported local model.
- Reject invalid API keys without leaking credentials.
- Reject unauthorized shell/file changes and malicious tool arguments.
- Confirm sensitive actions, cancel jobs, and inspect audit records.
- Validate fallback only with explicit user consent and compatible data handling.
- Benchmark tool-calling correctness per model; unsupported capabilities must be shown clearly.

## Research references
- https://docs.litellm.ai/docs/providers
- https://docs.litellm.ai/docs/routing
- https://github.com/ollama/ollama/blob/main/docs/api/openai-compatibility.mdx
- https://modelcontextprotocol.io/specification/2026-07-28
- https://help.openai.com/en/articles/5112595-best-practices-for-api
