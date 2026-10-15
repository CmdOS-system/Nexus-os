import tempfile
import unittest
from pathlib import Path
from recovery_g2.ovmf_isolation import isolated_ovmf_vars

class OvmfIsolationTests(unittest.TestCase):
    def test_copy_is_disposable_and_template_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            template = Path(root) / "template.fd"
            template.write_bytes(b"OVMF fixture")
            with isolated_ovmf_vars(template, lab_root=root) as copy:
                self.assertEqual(copy.read_bytes(), b"OVMF fixture")
                self.assertNotEqual(copy, template)
                copy.write_bytes(b"modified by guest")
                copy_path = copy
            self.assertFalse(copy_path.exists())
            self.assertEqual(template.read_bytes(), b"OVMF fixture")

    def test_rejects_symlink_template(self):
        with tempfile.TemporaryDirectory() as root:
            original = Path(root) / "original.fd"
            original.write_bytes(b"data")
            alias = Path(root) / "alias.fd"
            alias.symlink_to(original)
            with self.assertRaisesRegex(ValueError, "symlink"):
                with isolated_ovmf_vars(alias, lab_root=root):
                    pass
