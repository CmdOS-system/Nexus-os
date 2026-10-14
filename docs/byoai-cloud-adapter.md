# Nexus Agent: compatible cloud chat adapter

An initial chat-completions adapter is available in `agent/openai_compatible.py`. It accepts an explicitly configured HTTPS endpoint on port 443, a `keyring:` secret reference and a SecretStore implementation.

This is a low-level adapter, not a production-ready onboarding flow. It sends role-separated user/assistant messages and does not support tool calling, model discovery, image input or automatic provider switching.

Safety boundaries: no HTTP endpoints, no URL-embedded credentials, no redirects, bounded response size, and no privileged system actions. Requests send content to the configured provider, so UI-level consent and privacy disclosures are required before enabling cloud usage.

The current in-memory SecretStore is for tests only. Production requires a desktop credential store implementation, endpoint trust/egress policy, and explicit cloud consent. DNS rebinding and provider trust remain unresolved security-review items.
