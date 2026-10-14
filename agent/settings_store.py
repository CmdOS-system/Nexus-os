"""Safe persistence for Nexus AI settings; never stores provider secrets."""
import os
import tempfile
from pathlib import Path
from settings import AISettings

def load_settings(path: Path) -> AISettings:
    if not isinstance(path, Path):
        raise TypeError("path must be Path")
    try:
        raw=path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return AISettings()
    except OSError as exc:
        raise RuntimeError("AI settings cannot be read") from exc
    return AISettings.from_json(raw)

def save_settings(path: Path, settings: AISettings) -> None:
    if not isinstance(path, Path):
        raise TypeError("path must be Path")
    if not isinstance(settings, AISettings):
        raise TypeError("settings must be AISettings")
    payload=settings.validate().to_json()+"\n"
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,tmp=tempfile.mkstemp(prefix=".ai-settings-",dir=path.parent)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp,path)
        os.chmod(path,0o600)
    except Exception:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
        raise
