# Nexus AI Settings

Nexus OS treats AI as optional. The default mode is `off`.

Supported policy modes are:
- `off`: no AI provider selected;
- `local`: local provider only;
- `cloud`: explicitly selected cloud provider with user consent;
- `hybrid`: local/cloud routing may be used, but cloud transmission still requires consent.

The serializable settings contain provider name, model, mode and consent state only. API keys and tokens are deliberately outside this model and must be resolved through SecretStore.

Changing AI settings does not grant filesystem, shell, package-management, camera, microphone or administrative permissions. Those capabilities require separate policy and authorization.

A future graphical Nexus AI Settings application should edit this policy model and use an OS-backed credential store for secrets.
