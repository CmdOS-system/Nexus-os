#!/usr/bin/env python3
"""Write a small real WebAssembly module exporting an incrementing counter."""
from pathlib import Path
import sys

# (func () -> i32) plus a mutable i32 global; advance increments and returns it.
module = bytes.fromhex(
    "0061736d01000000"          # WebAssembly v1 header
    "0105016000017f"            # type 0: () -> i32
    "03020100"                  # one function, type 0
    "0606017f0141000b"          # mutable i32 global initialized to 0
    "07130207616476616e6365000005636f756e740300"  # advance func + count global
    "0a0d010b00230041016a240023000b"  # ++global; return global
)
Path(sys.argv[1]).write_bytes(module)
