from pathlib import Path
import tempfile
import unittest
from windows_office_lab import fatal_office_service_error


class OfficeServiceWatchTests(unittest.TestCase):
    def test_real_utf16_service_failure_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            temp = root / 'prefix/drive_c/users/nexuslab/AppData/Local/Temp'
            temp.mkdir(parents=True)
            (temp / 'office.log').write_text('ClickToRunSvc service cannot start - error code 1053.', encoding='utf-16')
            self.assertIn('1053', fatal_office_service_error(root))

    def test_nonfatal_catalog_warning_does_not_abort(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            temp = root / 'prefix/drive_c/users/nexuslab/AppData/Local/Temp'
            temp.mkdir(parents=True)
            (temp / 'office.log').write_text('ErrorCode188: catalog errors are non-fatal, continuing.', encoding='utf-16')
            self.assertIsNone(fatal_office_service_error(root))

    def test_external_symlink_and_absent_logs_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'profile'
            self.assertIsNone(fatal_office_service_error(root))
            temp = root / 'prefix/drive_c/users/nexuslab/Temp'
            temp.mkdir(parents=True)
            outside = Path(directory) / 'outside.log'
            outside.write_text('ClickToRunSvc service cannot start - error code 1053.')
            (temp / 'linked.log').symlink_to(outside)
            self.assertIsNone(fatal_office_service_error(root))
