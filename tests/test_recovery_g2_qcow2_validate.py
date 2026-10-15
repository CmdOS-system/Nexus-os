import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from recovery_g2.qcow2_validate import validate_qcow2

class Qcow2ValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "disk.qcow2"
        self.path.write_bytes(bytes.fromhex("514649fb") + b"fixture")

    def run_info(self, metadata):
        def runner(args, **kwargs):
            self.assertEqual(args[1:4], ["info", "--output=json", "-f"])
            self.assertTrue(kwargs["check"])
            return SimpleNamespace(stdout=json.dumps(metadata))
        return runner

    def test_valid_image(self):
        result = validate_qcow2(self.path, runner=self.run_info(
            {"format": "qcow2", "virtual-size": 2 * 1024**3}))
        self.assertEqual(result["format"], "qcow2")

    def test_backing_file_rejected(self):
        with self.assertRaisesRegex(ValueError, "backing"):
            validate_qcow2(self.path, runner=self.run_info(
                {"format": "qcow2", "virtual-size": 2 * 1024**3,
                 "backing-filename": "/host/sensitive.qcow2"}))

    def test_wrong_format_rejected(self):
        with self.assertRaises(ValueError):
            validate_qcow2(self.path, runner=self.run_info(
                {"format": "raw", "virtual-size": 2 * 1024**3}))

    def test_invalid_magic_rejected_before_runner(self):
        self.path.write_bytes(b"not a disk")
        with self.assertRaisesRegex(ValueError, "signature"):
            validate_qcow2(self.path, runner=lambda *a, **k: self.fail("must not run"))
