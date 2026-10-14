"""Linux Secret Service adapter via libsecret's secret-tool; fail closed."""
import shutil
import subprocess
from secret_store import SecretStore

PREFIX = "keyring:nexus/"

def _name(reference):
    if not isinstance(reference, str) or not reference.startswith(PREFIX):
        raise ValueError("Expected keyring:nexus/<provider> reference")
    name = reference[len(PREFIX):]
    if not name or len(name) > 128 or not all(c.isalnum() or c in "-_." for c in name):
        raise ValueError("Invalid Nexus keyring reference")
    return name

class LinuxSecretStore(SecretStore):
    """Uses the logged-in user's Secret Service; never falls back to disk."""
    def __init__(self, executable="secret-tool"):
        if executable != "secret-tool":
            raise ValueError("Only system secret-tool is supported")
        self.executable = shutil.which(executable)

    def _run(self, args, value=None):
        if self.executable is None:
            raise RuntimeError("Secret Service client is unavailable")
        try:
            result = subprocess.run(
                [self.executable, *args],
                input=value, text=True, capture_output=True, timeout=15,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise RuntimeError("Secret Service operation failed") from exc
        if result.returncode != 0:
            raise RuntimeError("Secret Service rejected the operation")
        return result.stdout

    def resolve(self, reference: str) -> str:
        name = _name(reference)
        value = self._run(["lookup", "application", "nexus-os", "provider", name]).rstrip("\n")
        if not value:
            raise KeyError("Secret not found in keyring")
        return value

    def store(self, reference: str, value: str) -> None:
        name = _name(reference)
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Secret must be nonempty")
        self._run(
            ["store", "--label=Nexus OS AI: " + name,
             "application", "nexus-os", "provider", name],
            value + "\n",
        )

    def delete(self, reference: str) -> None:
        name = _name(reference)
        self._run(["clear", "application", "nexus-os", "provider", name])
