"""Linux-only advisory lock for serialized Recovery G2 transactions.

All writers MUST cooperate; this does not protect against hostile processes.
"""
import fcntl
import os
from contextlib import contextmanager
from pathlib import Path

@contextmanager
def recovery_lock(directory):
    path = Path(directory) / ".recovery.lock"
    fd = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, "O_CLOEXEC", 0), 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)
