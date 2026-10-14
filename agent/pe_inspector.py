"""Read-only bounded Windows PE header identification. Never executes target files."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import struct

MAX_HEADER_OFFSET = 1024 * 1024
MACHINES = {0x014C: "x86", 0x8664: "x86_64", 0xAA64: "arm64", 0x01C4: "arm"}
MAGICS = {0x10B: "PE32", 0x20B: "PE32+"}


class InvalidPE(ValueError):
    """Malformed, truncated, or unsupported PE image."""


@dataclass(frozen=True)
class PEInfo:
    machine: str
    format: str
    sections: int
    subsystem: int
    is_dll: bool


def inspect_pe(path: str | Path) -> PEInfo:
    """Parse fixed headers only; bounded reads and no target execution."""
    with open(path, "rb") as file:
        dos = file.read(64)
        if len(dos) != 64 or dos[:2] != b"MZ":
            raise InvalidPE("Missing DOS MZ header")
        offset = struct.unpack_from("<I", dos, 0x3C)[0]
        if offset < 64 or offset > MAX_HEADER_OFFSET:
            raise InvalidPE("Invalid or excessive PE header offset")
        file.seek(offset)
        head = file.read(24)
        if len(head) != 24 or head[:4] != b"PE\x00\x00":
            raise InvalidPE("Missing PE signature or truncated COFF header")
        machine, sections, _, _, _, opt_size, characteristics = struct.unpack_from("<HHIIIHH", head, 4)
        if machine not in MACHINES or not (1 <= sections <= 96):
            raise InvalidPE("Unsupported machine or section count")
        if opt_size < 70 or opt_size > 4096:
            raise InvalidPE("Invalid optional header length")
        opt = file.read(opt_size)
        if len(opt) != opt_size:
            raise InvalidPE("Truncated optional header")
        magic = struct.unpack_from("<H", opt)[0]
        if magic not in MAGICS:
            raise InvalidPE("Unsupported PE optional header magic")
        subsystem_offset = 68
        if opt_size < subsystem_offset + 2:
            raise InvalidPE("Truncated subsystem")
        subsystem = struct.unpack_from("<H", opt, subsystem_offset)[0]
        # Verify section header table exists, without reading any section payload.
        if len(file.read(sections * 40)) != sections * 40:
            raise InvalidPE("Truncated section headers")
        return PEInfo(MACHINES[machine], MAGICS[magic], sections, subsystem, bool(characteristics & 0x2000))
