# Nexus Agent prototype

This directory contains the first offline, standard-library-only provider configuration and policy prototype. It is not yet wired into the desktop or a language model.

Run `python3 -m unittest discover -s agent/tests -v` from repository root.

Provider endpoints must be explicitly configured. This prototype does not store API keys or make network requests.
