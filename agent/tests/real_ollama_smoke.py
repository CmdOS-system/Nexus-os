"""Explicit integration probe: requires a running Ollama with qwen2.5:0.5b.

Uses synthetic prompts only. Not discovered by the offline unit-test suite.
Does not validate the ISO, GUI, voice, tool execution or model quality.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agent"))
from cli import resolve_local_model
from nexus_agent import Provider
from provider_client import chat
from settings import AISettings
from settings_store import save_settings


def main():
    model = "qwen2.5:0.5b"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open("http://127.0.0.1:11434/api/tags", timeout=10) as response:
        models = json.loads(response.read(1_000_000))["models"]
    selected = next(item for item in models if item["name"] == model)
    if not selected.get("digest"):
        raise RuntimeError("Model digest is missing")
    started = time.monotonic()
    answer = chat(Provider("ollama", "http://127.0.0.1:11434", True),
                  model, "Reply with exactly READY.", timeout=120)
    if not answer.strip():
        raise RuntimeError("Real provider returned no text")
    with tempfile.TemporaryDirectory() as directory:
        settings_path = Path(directory) / ".config/nexus/ai-settings.json"
        save_settings(settings_path, AISettings("local", "ollama", model, False))
        if resolve_local_model(settings_path=settings_path) != model:
            raise RuntimeError("Saved model was not selected")
        env = dict(os.environ, HOME=directory)
        env.pop("NEXUS_AI_MODEL", None)
        result = subprocess.run(
            [sys.executable, str(ROOT / "agent/cli.py")],
            input="Reply with exactly READY.\n/exit\n", text=True,
            capture_output=True, timeout=150, env=env, check=True,
        )
        if "Request failed:" in result.stdout or "Nexus>" not in result.stdout:
            raise RuntimeError("Saved-model CLI did not complete real inference")
        if not result.stdout.split("Nexus>", 1)[1].split("You>", 1)[0].strip():
            raise RuntimeError("CLI returned an empty answer")
    evidence = {
        "commit": os.environ.get("GITHUB_SHA", "local"),
        "model": model, "model_digest": selected["digest"],
        "provider_answer": answer, "cli_output": result.stdout,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "provider_inference_passed": True, "saved_model_cli_passed": True,
        "iso_or_gui_validated": False,
    }
    Path("nexus-real-ai-evidence.json").write_text(json.dumps(evidence, indent=2))
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
