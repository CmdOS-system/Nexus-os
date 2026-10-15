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
        self.path.write_bytes(bytes.fromhex("514649fb") + (3).to_bytes(4, "big") + bytes(92) + (104).to_bytes(4, "big"))

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

    def test_required_check_errors_absent_is_rejected(self):
        def runner(args, **kwargs):
            if args[1] == "check":
                return SimpleNamespace(stdout=json.dumps({"corruptions": 0, "leaks": 0}))
            return SimpleNamespace(stdout=json.dumps({"format": "qcow2", "virtual-size": 2 * 1024**3}))
        with self.assertRaisesRegex(ValueError, "consistency"):
            validate_qcow2(self.path, runner=runner)

    def test_optional_zero_corruptions_and_leaks_omitted(self):
        def runner(args, **kwargs):
            if args[1] == "check":
                return SimpleNamespace(stdout=json.dumps({"check-errors": 0}))
            return SimpleNamespace(stdout=json.dumps({"format": "qcow2", "virtual-size": 2 * 1024**3}))
        self.assertEqual(validate_qcow2(self.path, runner=runner)["format"], "qcow2")

    def test_missing_check_fields_rejected(self):
        def runner(args, **kwargs):
            if args[1] == "check":
                return SimpleNamespace(stdout=json.dumps({}))
            return SimpleNamespace(stdout=json.dumps({"format": "qcow2", "virtual-size": 2 * 1024**3}))
        with self.assertRaisesRegex(ValueError, "consistency"):
            validate_qcow2(self.path, runner=runner)

    def test_external_data_bit_rejected_before_runner(self):
        header = bytearray(bytes.fromhex("514649fb") + (3).to_bytes(4, "big") + bytes(92) + (104).to_bytes(4, "big"))
        header[72:80] = (1 << 2).to_bytes(8, "big")
        self.path.write_bytes(header)
        with self.assertRaisesRegex(ValueError, "external QCOW2 data"):
            validate_qcow2(self.path, runner=lambda *a, **k: self.fail("must not run"))

    def test_truncated_header_rejected(self):
        self.path.write_bytes(bytes.fromhex("514649fb") + b"short")
        with self.assertRaisesRegex(ValueError, "truncated"):
            validate_qcow2(self.path, runner=lambda *a, **k: self.fail("must not run"))

    def test_version_2_header_72_bytes_accepted(self):
        self.path.write_bytes(bytes.fromhex("514649fb") + (2).to_bytes(4, "big") + bytes(64))
        result = validate_qcow2(self.path, runner=self.run_info(
            {"format": "qcow2", "virtual-size": 2 * 1024**3}))
        self.assertEqual(result["format"], "qcow2")

    def test_version_3_header_80_bytes_rejected(self):
        self.path.write_bytes(bytes.fromhex("514649fb") + (3).to_bytes(4, "big") + bytes(72))
        with self.assertRaisesRegex(ValueError, "truncated QCOW2 v3"):
            validate_qcow2(self.path, runner=lambda *a, **k: self.fail("must not run"))

    def test_header_backing_pointer_rejected_without_runner(self):
        header = bytearray(bytes.fromhex("514649fb") + (3).to_bytes(4, "big") + bytes(92) + (104).to_bytes(4, "big"))
        header[8:16] = (65536).to_bytes(8, "big")
        self.path.write_bytes(header)
        with self.assertRaisesRegex(ValueError, "backing"):
            validate_qcow2(self.path, runner=lambda *a, **k: self.fail("must not run"))

    def test_header_corrupt_flag_rejected_without_runner(self):
        header = bytearray(bytes.fromhex("514649fb") + (3).to_bytes(4, "big") + bytes(92) + (104).to_bytes(4, "big"))
        header[72:80] = (1 << 1).to_bytes(8, "big")
        self.path.write_bytes(header)
        with self.assertRaisesRegex(ValueError, "dirty or corrupt"):
            validate_qcow2(self.path, runner=lambda *a, **k: self.fail("must not run"))

    def test_header_encryption_rejected_without_runner(self):
        header = bytearray(bytes.fromhex("514649fb") + (3).to_bytes(4, "big") + bytes(92) + (104).to_bytes(4, "big"))
        header[32:36] = (1).to_bytes(4, "big")
        self.path.write_bytes(header)
        with self.assertRaisesRegex(ValueError, "encrypted"):
            validate_qcow2(self.path, runner=lambda *a, **k: self.fail("must not run"))

    def test_invalid_v3_declared_header_length_rejected(self):
        header = bytearray(bytes.fromhex("514649fb") + (3).to_bytes(4, "big") + bytes(92) + (104).to_bytes(4, "big"))
        header[100:104] = (103).to_bytes(4, "big")
        self.path.write_bytes(header)
        with self.assertRaisesRegex(ValueError, "header length"):
            validate_qcow2(self.path, runner=lambda *a, **k: self.fail("must not run"))

    def test_wrong_format_rejected(self):
        with self.assertRaises(ValueError):
            validate_qcow2(self.path, runner=self.run_info(
                {"format": "raw", "virtual-size": 2 * 1024**3}))

    def test_invalid_magic_rejected_before_runner(self):
        self.path.write_bytes(b"not a disk")
        with self.assertRaisesRegex(ValueError, "signature"):
            validate_qcow2(self.path, runner=lambda *a, **k: self.fail("must not run"))
