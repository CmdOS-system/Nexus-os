#!/usr/bin/env python3
"""Extract the raw ARM64 instruction bytes from a 64-bit Mach-O __TEXT,__text section."""
import struct
import sys
from pathlib import Path

source, destination = map(Path, sys.argv[1:3])
data = source.read_bytes()
if len(data) < 32 or data[:4] != b"\xcf\xfa\xed\xfe":
    raise SystemExit("expected a little-endian 64-bit Mach-O")
_, cpu, _, _, ncmds, sizeofcmds, _, _ = struct.unpack_from("<IiiIIIII", data, 0)
if cpu != 0x0100000C:
    raise SystemExit(f"expected ARM64 Mach-O, cpu type is {cpu:#x}")
offset = 32
end_commands = offset + sizeofcmds
for _ in range(ncmds):
    command, command_size = struct.unpack_from("<II", data, offset)
    if command == 0x19:  # LC_SEGMENT_64
        segment = data[offset + 8:offset + 24].rstrip(b"\0").decode("ascii")
        section_count = struct.unpack_from("<I", data, offset + 64)[0]
        section_offset = offset + 72
        for _ in range(section_count):
            section = data[section_offset:section_offset + 16].rstrip(b"\0").decode("ascii")
            section_segment = data[section_offset + 16:section_offset + 32].rstrip(b"\0").decode("ascii")
            size = struct.unpack_from("<Q", data, section_offset + 40)[0]
            file_offset = struct.unpack_from("<I", data, section_offset + 48)[0]
            if segment == "__TEXT" and section == "__text" and section_segment == "__TEXT":
                if size < 8 or file_offset + size > len(data):
                    raise SystemExit("invalid __TEXT,__text range")
                destination.write_bytes(data[file_offset:file_offset + size])
                print(f"Extracted {size} bytes from __TEXT,__text")
                raise SystemExit(0)
            section_offset += 80
    offset += command_size
    if offset > end_commands:
        raise SystemExit("invalid Mach-O load-command table")
raise SystemExit("Mach-O __TEXT,__text section not found")
