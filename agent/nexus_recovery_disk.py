#!/usr/bin/env python3
"""Disposable file-backed A/B storage model for Nexus Recovery G2.

This module only accepts regular files created by the caller. It never opens
block devices and intentionally contains no partitioning or bootloader code.
"""
from __future__ import annotations
import hashlib
import os

MAGIC = b"NEXUS_SLOT_V1\0"
SLOT_SIZE = 1024 * 1024
SLOTS = {"A": 0, "B": SLOT_SIZE}
DISK_SIZE = SLOT_SIZE * 2


def _require_regular(path: str) -> None:
    st = os.stat(path, follow_symlinks=False)
    if not os.path.isfile(path) or os.path.islink(path):
        raise ValueError("recovery test storage must be a regular non-symlink file")
    if st.st_size != DISK_SIZE:
        raise ValueError("unexpected recovery test disk size")


def create_disk(path: str) -> None:
    if os.path.exists(path):
        raise ValueError("refusing to overwrite existing path")
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.ftruncate(fd, DISK_SIZE)
        os.fsync(fd)
    finally:
        os.close(fd)


def write_slot(path: str, slot: str, payload: bytes) -> str:
    _require_regular(path)
    if slot not in SLOTS:
        raise ValueError("invalid slot")
    digest = hashlib.sha256(payload).hexdigest()
    header = MAGIC + len(payload).to_bytes(8, "big") + bytes.fromhex(digest)
    if len(header) + len(payload) > SLOT_SIZE:
        raise ValueError("payload exceeds slot boundary")
    with open(path, "r+b", buffering=0) as f:
        f.seek(SLOTS[slot])
        f.write(header)
        f.write(payload)
        remaining = SLOT_SIZE - len(header) - len(payload)
        f.write(b"\0" * remaining)
        os.fsync(f.fileno())
    return digest


def read_slot(path: str, slot: str) -> bytes:
    _require_regular(path)
    if slot not in SLOTS:
        raise ValueError("invalid slot")
    with open(path, "rb") as f:
        f.seek(SLOTS[slot])
        raw = f.read(SLOT_SIZE)
    if not raw.startswith(MAGIC):
        raise ValueError("slot is not initialized")
    p = len(MAGIC)
    size = int.from_bytes(raw[p:p+8], "big"); p += 8
    digest = raw[p:p+32]; p += 32
    if size > SLOT_SIZE - p:
        raise ValueError("invalid slot payload size")
    payload = raw[p:p+size]
    if hashlib.sha256(payload).digest() != digest:
        raise ValueError("slot checksum mismatch")
    return payload
