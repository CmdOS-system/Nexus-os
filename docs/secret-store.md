# Nexus SecretStore

Nexus Agent must resolve credentials through a dedicated boundary instead of reading plaintext API keys from configuration.

The initial implementation contains only an in-memory store for tests and development. It does not persist credentials.

Production direction:
- integrate an OS-backed desktop credential store;
- keep provider configuration limited to opaque secret references;
- resolve a credential only when a provider request needs it;
- never place credentials in prompts, history, logs or crash reports;
- avoid exposing secrets to model-generated tool arguments;
- support deletion and provider-scoped credential rotation.

The in-memory implementation is not a production credential store.
