import errno
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import windows_vm_preflight as module


class WindowsVmPreflightTests(unittest.TestCase):
    def test_missing_device_is_not_permission_denial(self):
        with patch.object(module.os, 'open', side_effect=FileNotFoundError):
            self.assertEqual(module.check_kvm()['status'], 'missing')
        with patch.object(module.os, 'open', side_effect=PermissionError):
            self.assertEqual(module.check_kvm()['status'], 'permission_denied')

    def test_only_api_12_is_accepted_and_descriptor_is_closed(self):
        for version, accepted in ((12, True), (11, False)):
            with patch.object(module.os, 'open', return_value=42), patch.object(module.fcntl, 'ioctl', return_value=version) as ioctl, patch.object(module.os, 'close') as close:
                self.assertEqual(module.check_kvm()['available'], accepted)
                ioctl.assert_called_once_with(42, module.KVM_GET_API_VERSION, 0)
                close.assert_called_once_with(42)

    def test_failed_ioctl_still_closes_descriptor(self):
        with patch.object(module.os, 'open', return_value=42), patch.object(module.fcntl, 'ioctl', side_effect=OSError(errno.ENOTTY, 'not KVM')), patch.object(module.os, 'close') as close:
            self.assertFalse(module.check_kvm()['available'])
            close.assert_called_once_with(42)

    def test_detected_prerequisites_never_claim_office_or_windows_installed(self):
        with patch.object(module, 'check_kvm', return_value={'available': True}), patch.object(module.shutil, 'which', return_value='/example/tool'), patch.object(module.platform, 'machine', return_value='x86_64'):
            report = module.collect()
        self.assertTrue(report['static_prerequisites_detected'])
        self.assertFalse(report['word_validated'])
        self.assertFalse(report['windows_installation_verified'])
        self.assertIn('confirm_freerdp_3_and_vm_manager_access', report['remaining'])


if __name__ == '__main__':
    unittest.main()
