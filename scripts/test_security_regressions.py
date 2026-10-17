import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('security_scan', Path(__file__).with_name('check-security-regressions.py'))
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)


class SecurityScanTests(unittest.TestCase):
    def test_only_known_gui_buttons_are_allowed(self):
        self.assertEqual(list(scan.violations('app.confirm.invoke()\napp.open_button.invoke()', 'tests/windows_installer_gui_smoke.py')), [])

    def test_legacy_calls_still_fail(self):
        cases = [
            ('broker.invoke()', 'tests/windows_installer_gui_smoke.py'),
            ('app.confirm.invoke()', 'runtime.py'),
            ('app.confirm.invoke("unsafe")', 'tests/windows_installer_gui_smoke.py'),
            ('broker.invoke ( )', 'runtime.py'),
            ('from secrets import token', 'tests/windows_installer_gui_smoke.py'),
        ]
        for source, path in cases:
            with self.subTest(source=source, path=path):
                self.assertTrue(list(scan.violations(source, path)))


if __name__ == '__main__':
    unittest.main()
