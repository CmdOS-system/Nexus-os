# Nexus desktop integration

The first desktop integration is deliberately small and auditable.

The Live image contains a standard desktop entry for Nexus Agent and a launcher at `/usr/local/bin/nexus-agent`. The launcher does not use sudo, does not request polkit authorization and does not execute arbitrary model-generated commands.

The launcher expects the agent runtime under `/opt/nexus/agent` and a local model selected through `NEXUS_AI_MODEL`. Until the runtime is included in the image, it fails clearly instead of pretending that the assistant is available.

Future work includes a graphical provider/settings application, desktop keyring integration, first-run setup and a native Nexus shell experience.
