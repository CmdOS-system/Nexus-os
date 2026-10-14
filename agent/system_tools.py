"""Low-risk Nexus system tools with fixed data sources."""
from pathlib import Path

IDENTITY_PATH = Path("/etc/nexus-os-release")

def nexus_identity(path: Path = IDENTITY_PATH) -> dict:
    """Read the fixed Nexus identity document into a small allowlisted result."""
    if not isinstance(path, Path):
        raise TypeError("path must be Path")
    data = {}
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError("Nexus identity is unavailable") from exc

    allowed = {"NAME", "VERSION", "VERSION_ID", "PRETTY_NAME"}
    for line in raw.splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in allowed:
            data[key] = value.strip().strip('"')

    if "NAME" not in data or "VERSION_ID" not in data:
        raise ValueError("Invalid Nexus identity document")
    return data

def register_system_tools(broker):
    broker.register(
        "system.identity",
        lambda: nexus_identity(),
        {"type": "object", "properties": {}, "required": []},
    )
