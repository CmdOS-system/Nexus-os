"""User-mediated file grants for R1 read access."""
from dataclasses import dataclass
from pathlib import Path
import secrets

@dataclass(frozen=True)
class FileGrant:
    token: str
    path: Path

class FileGrantStore:
    def __init__(self):
        self._grants = {}

    def grant(self, path: Path) -> str:
        if not isinstance(path, Path) or not path.is_absolute():
            raise ValueError("An absolute user-selected path is required")
        if not path.is_file():
            raise ValueError("Selected path must be a regular file")
        token = secrets.token_urlsafe(24)
        self._grants[token] = path
        return token

    def consume_text(self, token: str, max_bytes: int = 1_000_000) -> str:
        if not isinstance(token, str) or not token:
            raise ValueError("Grant token required")
        if type(max_bytes) is not int or not 1 <= max_bytes <= 1_000_000:
            raise ValueError("Invalid read limit")
        try:
            path = self._grants.pop(token)
        except KeyError:
            raise PermissionError("Unknown or already consumed file grant") from None
        try:
            size = path.stat().st_size
            if size > max_bytes:
                raise ValueError("Selected file exceeds read limit")
            return path.read_text(encoding="utf-8")
        except UnicodeError as exc:
            raise ValueError("Selected file is not UTF-8 text") from exc
        except OSError as exc:
            raise RuntimeError("Selected file cannot be read") from exc

def register_file_tools(broker, grants: FileGrantStore):
    if not isinstance(grants, FileGrantStore):
        raise TypeError("FileGrantStore required")
    broker.register(
        "file.read_text",
        lambda grant_token: grants.consume_text(grant_token),
        {
            "type": "object",
            "properties": {"grant_token": {"type": "string"}},
            "required": ["grant_token"],
        },
    )
