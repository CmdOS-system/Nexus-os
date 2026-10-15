"""Redundant, checksummed Recovery G2 metadata prototype. Not a bootloader."""
import hashlib
import json
import os
from pathlib import Path
from .boot_state import BootState

class RecoveryRequired(RuntimeError):
    pass

def encode(state):
    payload = dict(confirmed=state.confirmed, candidate=state.candidate,
                   attempts_left=state.attempts_left, generation=state.generation)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return json.dumps(dict(payload=payload, sha256=hashlib.sha256(raw).hexdigest())).encode()

def decode(raw):
    record = json.loads(raw)
    payload = record["payload"]
    if set(payload) != {"confirmed", "candidate", "attempts_left", "generation"}:
        raise ValueError("unexpected keys")
    if type(payload["generation"]) is not int or type(payload["attempts_left"]) is not int:
        raise ValueError("invalid counter types")
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(canonical).hexdigest() != record["sha256"]:
        raise ValueError("checksum mismatch")
    return BootState(**payload)

class RedundantStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.paths = [self.directory / "state.0.json", self.directory / "state.1.json"]

    def _copies(self):
        states = []
        for path in self.paths:
            try:
                states.append(decode(path.read_bytes()))
            except (OSError, ValueError, TypeError, KeyError):
                states.append(None)
        return states

    def load(self):
        valid = [s for s in self._copies() if s is not None]
        if not valid:
            raise RecoveryRequired("no valid metadata")
        generation = max(s.generation for s in valid)
        newest = [s for s in valid if s.generation == generation]
        if any(s != newest[0] for s in newest[1:]):
            raise RecoveryRequired("conflicting metadata")
        return newest[0]

    def save(self, state):
        copies = self._copies()
        if any(p.exists() for p in self.paths):
            previous = self.load()
            if state.generation <= previous.generation:
                raise ValueError("generation must increase")
        order = sorted(range(2), key=lambda i: -1 if copies[i] is None else copies[i].generation)
        data = encode(state)
        for i in order:
            destination = self.paths[i]
            temporary = self.directory / (destination.name + ".tmp")
            with open(temporary, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
            directory_fd = os.open(self.directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
