"""Interactive local-only Nexus Agent chat prototype (no system tools)."""
import argparse
from pathlib import Path
from nexus_agent import Provider
from provider_client import chat
from settings_store import load_settings

def resolve_local_model(explicit_model=None, settings_path=None):
    """Use the user's saved local AI model; never silently route cloud settings."""
    if explicit_model:
        return explicit_model
    path = settings_path or Path.home() / ".config/nexus/ai-settings.json"
    settings = load_settings(path)
    if settings.mode != "local":
        raise ValueError("Configure local AI in Nexus Control Center before starting Nexus Agent")
    if settings.provider != "ollama":
        raise ValueError("The local chat prototype currently supports only Ollama")
    return settings.model

def main():
    parser = argparse.ArgumentParser(description="Nexus Agent local model prototype")
    parser.add_argument("--model", help="Override the saved local model")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    args = parser.parse_args()
    try:
        model = resolve_local_model(args.model)
    except (ValueError, RuntimeError, OSError) as exc:
        parser.error(str(exc))
    provider = Provider("ollama", args.endpoint, local=True).validate()
    print("Nexus Agent local prototype. Type /exit to quit.")
    while True:
        try:
            message = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if message == "/exit":
            break
        if not message:
            continue
        try:
            print("Nexus>", chat(provider, model, message))
        except Exception as exc:
            print(f"Request failed: {type(exc).__name__}")

if __name__ == "__main__":
    main()
