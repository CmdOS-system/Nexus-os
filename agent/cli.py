"""Interactive local-only Nexus Agent chat prototype (no system tools)."""
import argparse
from nexus_agent import Provider
from provider_client import chat

def main():
    parser = argparse.ArgumentParser(description="Nexus Agent local model prototype")
    parser.add_argument("--model", required=True)
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    args = parser.parse_args()
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
            print("Nexus>", chat(provider, args.model, message))
        except Exception as exc:
            print(f"Request failed: {type(exc).__name__}")

if __name__ == "__main__":
    main()
