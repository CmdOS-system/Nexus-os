# Nexus Agent prototype

Nexus Agent includes a local Ollama chat CLI, provider-independent conversation primitives, a configurable provider layer, secret references, routing policy and user-bound tool/file permissions. These are prototype components, not proof of end-to-end voice or desktop automation.

## Local chat

Configure local Ollama and a model in Nexus Control Center. The desktop Agent launcher uses the saved model from `~/.config/nexus/ai-settings.json`; no manual environment variable is required. The CLI rejects off/cloud/hybrid settings and unsupported local providers when resolving a saved model.

For an explicit model override, run `python3 agent/cli.py --model MODEL`. This makes real requests to the configured local Ollama endpoint; Ollama and the chosen model must already be available. Type `/exit` to stop. The CLI does not execute system tools.

## Tests and evidence

Run `python3 -m unittest discover -s agent/tests -p 'test_*.py' -v` from the repository root. These tests primarily use fixtures and mocks; they do not establish real-model connectivity.

Security and saved-model integration were merged through PRs #2 and #3. Their combined local suite passed 184 tests; main Fast Checks run 38978527776 passed all five jobs.

PR #4 adds an explicit real-model integration probe, `agent/tests/real_ollama_smoke.py`, and an isolated CPU Ollama workflow. At this documentation update its run 38978824081 was in progress, so real inference remained unconfirmed. Do not run the probe with personal prompts or credentials: it uses fixed synthetic inputs and records its output.

See `../docs/PROJECT-CONTINUITY.md` for current progress and `../docs/ai-provider-architecture.md` for design. Keep credentials out of source and logs. Implementation, mocked tests, real-provider tests and installed-system tests are separate levels of evidence.
