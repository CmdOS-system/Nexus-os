#!/usr/bin/env python3
"""Crash-safe metadata primitives for Nexus Recovery experiments.

Unprivileged and deliberately independent from block devices and bootloaders.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import tempfile
from dataclasses import asdict, dataclass


SCHEMA = 1
VALID_SLOTS = {"A", "B"}
VALID_STATES = {"idle", "fetched", "verified", "staged", "pending_boot", "booting", "healthy"}


@dataclass(frozen=True)
class Metadata:
    generation: int
    good: str
    candidate: str | None
    state: str
    attempts_left: int
    transaction_id: int

    def validate(self) -> None:
        if self.generation < 0 or self.transaction_id < 0:
            raise ValueError("negative generation/transaction")
        if self.good not in VALID_SLOTS:
            raise ValueError("invalid good slot")
        if self.candidate is not None and self.candidate not in VALID_SLOTS:
            raise ValueError("invalid candidate slot")
        if self.candidate == self.good:
            raise ValueError("candidate must differ from good slot")
        if self.state not in VALID_STATES:
            raise ValueError("invalid state")
        if self.attempts_left < 0:
            raise ValueError("negative attempts")


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def encode(meta: Metadata) -> bytes:
    meta.validate()
    body = {"schema": SCHEMA, "metadata": asdict(meta)}
    digest = hashlib.sha256(_canonical(body)).hexdigest()
    return _canonical({"body": body, "sha256": digest}) + b"\n"


def decode(raw: bytes) -> Metadata:
    try:
        envelope = json.loads(raw.decode("utf-8"))
        body = envelope["body"]
        digest = envelope["sha256"]
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError("malformed recovery metadata") from exc
    if body.get("schema") != SCHEMA:
        raise ValueError("unsupported metadata schema")
    expected = hashlib.sha256(_canonical(body)).hexdigest()
    if not isinstance(digest, str) or not hmac.compare_digest(digest, expected):
        raise ValueError("metadata checksum mismatch")
    try:
        meta = Metadata(**body["metadata"])
    except (KeyError, TypeError) as exc:
        raise ValueError("invalid metadata fields") from exc
    meta.validate()
    return meta


def atomic_write(path: str, meta: Metadata) -> None:
    """Replace one metadata file atomically and fsync file + parent directory."""
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".nexus-recovery-", dir=parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(encode(meta))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        dfd = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass


def load(path: str) -> Metadata:
    with open(path, "rb") as f:
        return decode(f.read())


def load_redundant(primary: str, secondary: str) -> Metadata:
    """Load the newest valid copy; reject ambiguity at the same transaction."""
    valid = []
    for path in (primary, secondary):
        try:
            valid.append(load(path))
        except (OSError, ValueError):
            pass
    if not valid:
        raise ValueError("no valid recovery metadata copy")
    newest_tx = max(m.transaction_id for m in valid)
    newest = [m for m in valid if m.transaction_id == newest_tx]
    if len(newest) == 2 and newest[0] != newest[1]:
        raise ValueError("conflicting recovery metadata at same transaction")
    return newest[0]


def write_redundant(primary: str, secondary: str, meta: Metadata) -> None:
    """Persist independently recoverable copies.

    The secondary is committed first; a crash before the primary update leaves
    at least one valid newest record and one older valid record.
    """
    if os.path.abspath(primary) == os.path.abspath(secondary):
        raise ValueError("redundant metadata paths must differ")
    atomic_write(secondary, meta)
    atomic_write(primary, meta)
