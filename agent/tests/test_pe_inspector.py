import os
import struct
import tempfile
import unittest

from pe_inspector import InvalidPE, inspect_pe


def sample(machine=0x8664, magic=0x20B, sections=1):
    dos = bytearray(128)
    dos[:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, 128)
    coff = struct.pack("<HHIIIHH", machine, sections, 0, 0, 0, 72, 0x2002)
    optional = bytearray(72)
    struct.pack_into("<H", optional, 0, magic)
    struct.pack_into("<H", optional, 68, 2)
    return bytes(dos) + b"PE\x00\x00" + coff + optional + bytes(sections * 40)


class PEInspectorTests(unittest.TestCase):
    def inspect(self, payload):
        with tempfile.NamedTemporaryFile() as f:
            f.write(payload)
            f.flush()
            return inspect_pe(f.name)

    def test_x64(self):
        info = self.inspect(sample())
        self.assertEqual((info.machine, info.format, info.sections, info.subsystem, info.is_dll),
                         ("x86_64", "PE32+", 1, 2, True))

    def test_x86(self):
        info = self.inspect(sample(machine=0x14C, magic=0x10B))
        self.assertEqual((info.machine, info.format), ("x86", "PE32"))

    def test_invalid_magic(self):
        with self.assertRaises(InvalidPE):
            self.inspect(b"not an exe")

    def test_invalid_offset(self):
        data = bytearray(sample())
        struct.pack_into("<I", data, 0x3C, 0xFFFFFFFF)
        with self.assertRaises(InvalidPE):
            self.inspect(data)

    def test_truncated(self):
        with self.assertRaises(InvalidPE):
            self.inspect(sample()[:-10])

    def test_excess_sections(self):
        with self.assertRaises(InvalidPE):
            self.inspect(sample(sections=97))

    def test_unsupported_machine(self):
        with self.assertRaises(InvalidPE):
            self.inspect(sample(machine=0x9999))


if __name__ == "__main__":
    unittest.main()
