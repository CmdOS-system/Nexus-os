"""Per-user registry for trusted HTTPS storefront links."""
import json
import ipaddress
import os
import re
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


MAX_SOURCES = 100
MAX_NAME_LENGTH = 60
MAX_URL_LENGTH = 2048


def validate_source(name, url):
    """Return a normalized custom store record or raise ValueError."""
    name = " ".join(str(name).split())
    url = str(url).strip()
    if not name or len(name) > MAX_NAME_LENGTH:
        raise ValueError(f"El nombre debe tener entre 1 y {MAX_NAME_LENGTH} caracteres.")
    if any(ord(char) < 32 for char in name):
        raise ValueError("El nombre contiene caracteres de control.")
    if not url or len(url) > MAX_URL_LENGTH:
        raise ValueError("La dirección está vacía o supera el límite permitido.")
    if any(char.isspace() or ord(char) < 32 for char in url):
        raise ValueError("La dirección no puede contener espacios ni caracteres de control.")
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        # Accessing .port also validates malformed port values.
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("La dirección no tiene un formato válido.") from exc
    if parsed.scheme.lower() != "https" or not hostname:
        raise ValueError("Por seguridad, la tienda debe usar una dirección HTTPS completa.")
    if parsed.username or parsed.password:
        raise ValueError("No incluyas credenciales en la dirección de la tienda.")
    try:
        try:
            address = ipaddress.ip_address(hostname)
            normalized_host = f"[{address.compressed}]" if address.version == 6 else str(address)
        except ValueError:
            normalized_host = hostname.encode("idna").decode("ascii").lower().rstrip(".")
            label = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
            if not normalized_host or not re.fullmatch(rf"{label}(?:\.{label})*", normalized_host):
                raise ValueError("El dominio no es válido.")
        if parsed.port is not None:
            normalized_host += f":{parsed.port}"
    except (UnicodeError, ValueError) as exc:
        raise ValueError("El dominio no es válido.") from exc
    normalized = urlunsplit(("https", normalized_host, parsed.path or "/", parsed.query, ""))
    return {"id": uuid.uuid4().hex, "name": name, "url": normalized}


class SourceStore:
    """Small atomic JSON registry scoped to one user's config directory."""

    def __init__(self, path=None):
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        self.path = Path(path) if path else base / "nexus" / "omnistore-sources.json"

    def list(self):
        try:
            rows = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return []
        except (OSError, UnicodeError, json.JSONDecodeError):
            return []
        if not isinstance(rows, list):
            return []
        valid = []
        for row in rows[:MAX_SOURCES]:
            if not isinstance(row, dict):
                continue
            try:
                checked = validate_source(row.get("name", ""), row.get("url", ""))
            except (TypeError, ValueError):
                continue
            checked["id"] = str(row.get("id", ""))[:64] or checked["id"]
            valid.append(checked)
        return valid

    def add(self, name, url):
        source = validate_source(name, url)
        rows = self.list()
        if len(rows) >= MAX_SOURCES:
            raise ValueError(f"Puedes registrar hasta {MAX_SOURCES} tiendas.")
        key = source["url"].rstrip("/").casefold()
        if any(row["url"].rstrip("/").casefold() == key for row in rows):
            raise ValueError("Esa dirección ya está registrada.")
        rows.append(source)
        self._write(rows)
        return source

    def remove(self, source_id):
        rows = self.list()
        kept = [row for row in rows if row["id"] != source_id]
        if len(kept) != len(rows):
            self._write(kept)
        return len(kept) != len(rows)

    def _write(self, rows):
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.path.parent, 0o700)
        fd, temp_path = tempfile.mkstemp(prefix=".omnistore-", dir=self.path.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(rows, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_path, self.path)
        except Exception:
            try:
                os.close(fd)
            except OSError:
                pass
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
            raise
