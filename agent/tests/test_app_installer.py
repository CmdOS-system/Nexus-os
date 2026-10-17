import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app_installer as module


class InstallerTests(unittest.TestCase):
    def test_unapproved_file_never_becomes_ready(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(module.shutil, 'which', return_value='/usr/bin/wine'):
            source = Path(directory) / 'fake.exe'
            source.write_bytes(b'not an approved installer')
            service = module.Installer(Path(directory) / 'apps')
            try:
                with self.assertRaises(module.PackageError):
                    service.prepare(source)
                self.assertFalse(service.ready)
                self.assertFalse(service.package.exists())
            finally:
                service.close()

    def test_selected_source_is_not_the_executed_copy(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(module.shutil, 'which', return_value='/usr/bin/wine'):
            source = Path(directory) / 'name with spaces.exe'
            original = b'controlled fixture'
            source.write_bytes(original)
            service = module.Installer(Path(directory) / 'apps')
            try:
                with patch.object(module, 'PACKAGE_SHA256', hashlib.sha256(original).hexdigest()):
                    service.prepare(source)
                    source.write_bytes(b'replaced after selection')
                    self.assertEqual(service.package.read_bytes(), original)
                    service.package.chmod(0o600)
                    service.package.write_bytes(b'changed staged copy')
                    with patch.object(module.os, 'geteuid', return_value=1000), patch.object(module.subprocess, 'run') as run:
                        with self.assertRaises(module.PackageError):
                            service.install()
                        run.assert_not_called()
            finally:
                service.close()

    def test_prepare_does_not_run_installer_and_confirm_requires_ready(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(module.shutil, 'which', return_value='/usr/bin/wine'):
            service = module.Installer(Path(directory) / 'apps')
            try:
                with patch.object(module.subprocess, 'run') as run:
                    with self.assertRaises(module.PackageError):
                        service.install()
                    run.assert_not_called()
            finally:
                service.close()

    def test_symlink_input_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'target').write_bytes(b'test')
            (root / 'link.exe').symlink_to(root / 'target')
            with self.assertRaises(OSError):
                module.stage_verified(root / 'link.exe', root / 'staged')


if __name__ == '__main__':
    unittest.main()
