# Nexus OS technical research review

Status: research, not implemented or validated.

## Official references
- Linux From Scratch 13.1 systemd: https://linuxfromscratch.org/lfs/view/stable-systemd/
- Flatpak sandboxing: https://docs.flatpak.org/en/latest/basic-concepts.html
- XDG portals: https://flatpak.github.io/xdg-desktop-portal/docs/
- systemd portable services: https://systemd.io/PORTABLE_SERVICES/
- polkit: https://polkit.pages.freedesktop.org/polkit/
- Ollama tool calling: https://github.com/ollama/ollama/blob/main/docs/capabilities/tool-calling.mdx
- OpenAI MCP security: https://developers.openai.com/api/docs/guides/tools-connectors-mcp

## Architecture decisions
1. Start with a maintained Debian-derived image rather than a from-scratch distribution; keep customizations declarative and reproducible.
2. Separate desktop UI, AI provider adapters, agent orchestrator, and privileged tool broker into independently testable components.
3. Use least privilege; Flatpak portals for desktop integration and polkit for explicitly authorized administrative actions.
4. Never trust model output as authorization. Reject tool requests unless schema, policy, scope and confirmation checks pass.
5. Local Ollama adapter is a first-class provider; detect capabilities instead of assuming all models support tools/vision/JSON equally.
6. Keep local operation possible without internet; cloud provider configuration must be opt-in and disclose data transfer.
7. Prefer isolated test VMs for ISO and installer verification before physical-hardware trials.

## Research backlog
- Debian live-build and Calamares packaging/version compatibility
- Secure Boot signing and key ownership
- Update/rollback design, reproducible builds and SBOM
- Wine/Proton compatibility boundaries
- Hardware drivers, firmware redistribution and licensing
- Threat model for MCP servers, prompt injection, credential leakage, SSRF and privilege escalation

## Acceptance gates
- ISO reproducibly builds in clean CI runner.
- VM boots in UEFI and BIOS modes where supported.
- Installation completes and reboots without installation media.
- Unprivileged AI cannot modify system files, install packages or execute shell commands without explicit scoped authorization.
- Provider switching, offline local model, network failures and secret-redaction tests pass.
