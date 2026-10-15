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
            self.assertIn(args[1], ("info", "check"))
            self.assertTrue(kwargs["check"])
            if args[1] == "check":
                return SimpleNamespace(stdout=json.dumps({"corruptions": 0, "leaks": 0, "check-errors": 0}))
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

    def test_external_data_file_rejected(self):
        with self.assertRaisesRegex(ValueError, "external backing"):
            validate_qcow2(self.path, runner=self.run_info(
                {"format": "qcow2", "virtual-size": 2 * 1024**3,
                 "data-file": "/host/external.bin"}))

    def test_consistency_errors_rejected(self):
        def runner(args, **kwargs):
            if args[1] == "check":
                return SimpleNamespace(stdout=json.dumps({"corruptions": 1}))
            return SimpleNamespace(stdout=json.dumps({"format": "qcow2", "virtual-size": 2 * 1024**3}))
        with self.assertRaisesRegex(ValueError, "consistency"):
            validate_qcow2(self.path, runner=runner)

    def test_underscore_check_errors_rejected(self):
        def runner(args, **kwargs):
            if args[1] == "check":
                return SimpleNamespace(stdout=json.dumps({"check_errors": 1}))
            return SimpleNamespace(stdout=json.dumps({"format": "qcow2", "virtual-size": 2 * 1024**3}))
        with self.assertRaisesRegex(ValueError, "consistency"):
            validate_qcow2(self.path, runner=runner)

    def test_wrong_format_rejected(self):
        with self.assertRaises(ValueError):
            validate_qcow2(self.path, runner=self.run_info(
                {"format": "raw", "virtual-size": 2 * 1024**3}))

    def test_invalid_magic_rejected_before_runner(self):
        self.path.write_bytes(b"not a disk")
        with self.assertRaisesRegex(ValueError, "signature"):
            validate_qcow2(self.path, runner=lambda *a, **k: self.fail("must not run"))
