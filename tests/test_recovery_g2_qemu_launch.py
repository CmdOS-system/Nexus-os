import tempfile
import unittest
from pathlib import Path
from recovery_g2.qemu_launch import build_launch_plan

class QemuLaunchTests(unittest.TestCase):
    def test_builds_expected_pflash_and_virtio_arguments(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder) / name for name in ("CODE.fd", "VARS.fd", "disk.qcow2")]
            for path in paths:
                path.write_bytes(b"test fixture")
            argv = build_launch_plan(qemu_binary="qemu-system-x86_64",
                                     firmware_code=paths[0], firmware_vars=paths[1],
                                     disk_image=paths[2])
            self.assertIn("if=pflash,format=raw,readonly=on,file=" + str(paths[0]), argv)
            self.assertIn("if=virtio,format=qcow2,file=" + str(paths[2]), argv)

    def test_rejects_reused_firmware_and_disk(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder) / name for name in ("CODE.fd", "VARS.fd")]
            for path in paths:
                path.write_bytes(b"fixture")
            with self.assertRaises(ValueError):
                build_launch_plan(qemu_binary="qemu", firmware_code=paths[0],
                                  firmware_vars=paths[1], disk_image=paths[1])

    def test_rejects_invalid_memory(self):
        with self.assertRaises(ValueError):
            build_launch_plan(qemu_binary="qemu", firmware_code="missing",
                              firmware_vars="missing", disk_image="missing",
                              memory_mb=True)
