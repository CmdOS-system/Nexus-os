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

    def test_reopen_recognizes_receipt_without_executing(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(module.shutil, 'which', return_value='/usr/bin/wine'):
            root = Path(directory) / 'app'
            original = module.Installer(root)
            original.binary().parent.mkdir(parents=True)
            original.binary().write_bytes(b'controlled installed fixture')
            original.record_installation()
            original.close()
            with patch.object(module.subprocess, 'Popen') as launch:
                reopened = module.Installer(root)
                try:
                    self.assertTrue(reopened.installed)
                    self.assertFalse(reopened.ready)
                    launch.assert_not_called()
                    reopened.launch()
                    self.assertEqual(launch.call_args.args[0], ['/usr/bin/wine', str(reopened.binary())])
                    reopened.binary().write_bytes(b'changed binary')
                    with self.assertRaises(module.PackageError):
                        reopened.launch()
                    self.assertEqual(launch.call_count, 1)
                finally:
                    reopened.close()

    def test_missing_or_invalid_receipt_never_restores_installation(self):
        with tempfile.TemporaryDirectory() as directory:
            service = module.Installer(Path(directory))
            try:
                service.binary().parent.mkdir(parents=True)
                service.binary().write_bytes(b'fixture')
                self.assertFalse(service.has_verified_installation())
                (service.root / 'install-receipt.json').write_text('[]')
                self.assertFalse(service.has_verified_installation())
                (service.root / 'install-receipt.json').write_text('{bad')
                self.assertFalse(service.has_verified_installation())
            finally:
                service.close()

    def test_menu_entry_uses_fixed_command_in_spaced_data_directory(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(module.os.environ, {'XDG_DATA_HOME': directory + '/data with spaces'}):
            service = module.Installer(Path(directory) / 'app')
            try:
                with patch.object(module.subprocess, 'Popen') as launch:
                    service.register_menu_entry()
                    entry = service.menu_entry()
                    self.assertEqual(entry.parent, Path(directory) / 'data with spaces/applications')
                    self.assertIn('Exec=/usr/bin/python3 /opt/nexus/agent/app_installer.py --open-installed', entry.read_text())
                    import configparser
                    parsed = configparser.ConfigParser()
                    parsed.read(entry)
                    self.assertEqual(parsed['Desktop Entry']['Type'], 'Application')
                    self.assertNotIn(str(service.package), entry.read_text())
                    launch.assert_not_called()
            finally:
                service.close()

    def test_menu_action_opens_without_constructing_installer_window(self):
        with patch.object(module, 'Installer') as installer, patch.object(module, 'App') as app:
            self.assertEqual(module.main(['--open-installed']), 0)
            installer.return_value.launch.assert_called_once_with()
            installer.return_value.close.assert_called_once_with()
            app.assert_not_called()

    def test_notepad_selection_preserves_separate_7zip_profile(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(module.Path, 'home', return_value=Path(directory)), patch.object(module.shutil, 'which', return_value='/usr/bin/wine'):
            seven = module.Installer()
            seven.binary().parent.mkdir(parents=True)
            seven.binary().write_bytes(b'seven fixture')
            seven.record_installation()
            seven_root = seven.root
            seven.close()
            source = Path(directory) / 'arbitrary filename.exe'
            source.write_bytes(b'notepad fixture')
            specs = module.package_specs()
            specs['notepadpp']['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
            with patch.object(module, 'package_specs', return_value=specs), patch.object(module.subprocess, 'run') as run:
                service = module.Installer()
                try:
                    service.prepare(source)
                    self.assertEqual(service.package_id, 'notepadpp')
                    self.assertNotEqual(service.root, seven_root)
                    self.assertTrue(service.ready)
                    self.assertFalse((service.root / 'prefix').exists())
                    run.assert_not_called()
                    restored = module.Installer()
                    try:
                        self.assertTrue(restored.installed)
                        self.assertEqual(restored.root, seven_root)
                    finally:
                        restored.close()
                finally:
                    service.close()

    def test_notepad_receipt_and_menu_are_application_specific(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(module.os.environ, {'XDG_DATA_HOME': directory + '/data'}):
            service = module.Installer(Path(directory) / 'npp', package_id='notepadpp')
            try:
                service.binary().parent.mkdir(parents=True)
                service.binary().write_bytes(b'notepad executable fixture')
                service.record_installation()
                self.assertTrue(service.has_verified_installation())
                service.register_menu_entry()
                self.assertEqual(service.menu_entry().name, 'nexus-notepadpp.desktop')
                self.assertIn('--application notepadpp', service.menu_entry().read_text())
                self.assertIn('Notepad++ (Windows)', service.menu_entry().read_text())
            finally:
                service.close()

    def make_installed_fixture(self, directory):
        service = module.Installer(Path(directory) / 'profile')
        service.binary().parent.mkdir(parents=True)
        service.binary().write_bytes(b'installed fixture')
        service.record_installation()
        service.register_menu_entry()
        service.installed = True
        return service

    def test_remove_refuses_running_app_without_touching_profile_or_menu(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(module.os.environ, {'XDG_DATA_HOME': directory + '/data'}), patch.object(module.os, 'geteuid', return_value=1000), patch.object(module.shutil, 'which', side_effect=lambda name: '/usr/bin/' + name):
            service = self.make_installed_fixture(directory)
            try:
                with patch.object(module.subprocess, 'run', side_effect=module.subprocess.TimeoutExpired('wineserver', 5)) as run:
                    with self.assertRaises(module.PackageError):
                        service.remove()
                    self.assertEqual(run.call_count, 1)
                self.assertTrue(service.has_verified_installation())
                self.assertTrue(service.menu_entry().exists())
                self.assertFalse(list(service.root.parent.glob('.*.operation.lock')))
            finally:
                service.close()

    def test_trash_failure_restores_menu_and_keeps_installation(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(module.os.environ, {'XDG_DATA_HOME': directory + '/data'}), patch.object(module.os, 'geteuid', return_value=1000), patch.object(module.shutil, 'which', side_effect=lambda name: '/usr/bin/' + name):
            service = self.make_installed_fixture(directory)
            original = service.menu_entry().read_bytes()
            try:
                with patch.object(module.subprocess, 'run', side_effect=[None, module.subprocess.CalledProcessError(1, 'gio')]):
                    with self.assertRaises(module.subprocess.CalledProcessError):
                        service.remove()
                self.assertEqual(service.menu_entry().read_bytes(), original)
                self.assertTrue(service.has_verified_installation())
            finally:
                service.close()

    def test_remove_moves_only_target_profile_and_clears_state(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(module.os.environ, {'XDG_DATA_HOME': directory + '/data'}), patch.object(module.os, 'geteuid', return_value=1000), patch.object(module.shutil, 'which', side_effect=lambda name: '/usr/bin/' + name):
            service = self.make_installed_fixture(directory)
            other = Path(directory) / 'other-app'
            other.mkdir()
            (other / 'data').write_text('keep')
            destination = Path(directory) / 'trash-profile'
            def run(args, **kwargs):
                if args[1] == 'trash':
                    self.assertEqual(args, ['/usr/bin/gio', 'trash', str(service.root)])
                    service.root.rename(destination)
            try:
                with patch.object(module.subprocess, 'run', side_effect=run):
                    service.remove()
                self.assertFalse(service.root.exists())
                self.assertFalse(service.menu_entry().exists())
                self.assertFalse(service.installed)
                self.assertFalse(service.ready)
                self.assertTrue((destination / 'install-receipt.json').exists())
                self.assertFalse(list(destination.glob('*.lock')))
                self.assertEqual((other / 'data').read_text(), 'keep')
            finally:
                service.close()

    def test_cold_prefix_initialization_occurs_only_after_confirmation(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(module.os.environ, {'XDG_DATA_HOME': directory + '/data'}), patch.object(module.os, 'geteuid', return_value=1000), patch.object(module.shutil, 'which', return_value='/usr/bin/wine'):
            service = module.Installer(Path(directory) / 'profile')
            fixture = b'approved fixture'
            service.package.write_bytes(fixture)
            service.ready = True
            def run(args, **kwargs):
                if args[1] == 'wineboot':
                    self.assertEqual(args, ['/usr/bin/wine', 'wineboot', '--init'])
                    self.assertEqual(kwargs['timeout'], 300)
                    (service.root / 'prefix').mkdir()
                else:
                    self.assertTrue((service.root / 'prefix').exists())
                    service.binary().parent.mkdir(parents=True)
                    service.binary().write_bytes(b'installed binary')
            try:
                with patch.object(module, 'PACKAGE_SHA256', hashlib.sha256(fixture).hexdigest()), patch.object(module.subprocess, 'run', side_effect=run) as run_mock:
                    service.install()
                    self.assertEqual(run_mock.call_count, 2)
                    self.assertTrue(service.installed)
                    self.assertIn('NEXUS_WINE_INIT_END', (service.root / 'install.log').read_text())
            finally:
                service.close()

    def test_failed_prefix_initialization_never_starts_package(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(module.os, 'geteuid', return_value=1000), patch.object(module.shutil, 'which', return_value='/usr/bin/wine'):
            service = module.Installer(Path(directory) / 'profile')
            fixture = b'approved fixture'
            service.package.write_bytes(fixture)
            service.ready = True
            try:
                with patch.object(module, 'PACKAGE_SHA256', hashlib.sha256(fixture).hexdigest()), patch.object(module.subprocess, 'run', side_effect=module.subprocess.TimeoutExpired('wineboot', 300)) as run:
                    with self.assertRaises(module.subprocess.TimeoutExpired):
                        service.install()
                    self.assertEqual(run.call_count, 1)
                    self.assertFalse(service.installed)
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
