"""User-mediated file grants for R1 read access."""
from dataclasses import dataclass
from pathlib import Path
import os
import errno
import stat
import uuid

@dataclass(frozen=True)
class FileGrant:
    token: str
    path: Path
    device: int
    inode: int
    ctime_ns: int

class FileGrantStore:
    def __init__(self):
        self._grants = {}

    def grant(self, path: Path) -> str:
        if not isinstance(path, Path) or not path.is_absolute():
            raise ValueError("An absolute user-selected path is required")
        try:
            info = path.lstat()
        except OSError as exc:
            raise ValueError("Selected path is unavailable") from exc
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("Selected path must be a regular file")
        token = uuid.uuid4().hex
        self._grants[token] = FileGrant(token, path, info.st_dev, info.st_ino, info.st_ctime_ns)
        return token

    def consume_text(self, token: str, max_bytes: int = 1_000_000) -> str:
        if not isinstance(token, str) or not token:
            raise ValueError("Grant token required")
        if type(max_bytes) is not int or not 1 <= max_bytes <= 1_000_000:
            raise ValueError("Invalid read limit")
        try:
            grant = self._grants.pop(token)
        except KeyError:
            raise PermissionError("Unknown or already consumed file grant") from None
        try:
            try:
                fd = os.open(grant.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            except OSError as exc:
                if exc.errno == errno.ELOOP:
                    raise PermissionError("Selected file became a symbolic link") from exc
                raise
            with os.fdopen(fd, "rb") as handle:
                info = os.fstat(handle.fileno())
                if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino, info.st_ctime_ns) != (grant.device, grant.inode, grant.ctime_ns):
                    raise PermissionError("Selected file changed after approval")
                if info.st_size > max_bytes:
                    raise ValueError("Selected file exceeds read limit")
                data = handle.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise ValueError("Selected file exceeds read limit")
            return data.decode("utf-8")
        except UnicodeError as exc:
            raise ValueError("Selected file is not UTF-8 text") from exc
        except PermissionError:
            raise
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
