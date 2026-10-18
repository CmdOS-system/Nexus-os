from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compatibility_advisor import inspect_package


class CompatibilityAdvisorTests(unittest.TestCase):
    def write(self, directory, name, data):
        path = Path(directory) / name
        path.write_bytes(data)
        return path

    def test_pe_is_identified_from_signature_and_architecture_not_name(self):
        with tempfile.TemporaryDirectory() as directory:
            data = bytearray(128)
            data[:2] = b"MZ"
            data[0x3C:0x40] = (64).to_bytes(4, "little")
            data[64:68] = b"PE\0\0"
            data[68:70] = (0x8664).to_bytes(2, "little")
            result = inspect_package(self.write(directory, "not-an-exe.data", data))
            self.assertEqual((result["format"], result["architecture"]), ("windows-pe", "x86_64"))
            self.assertFalse(result["executed"])

    def test_apk_requires_manifest_and_android_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "demo.apk"
            with zipfile.ZipFile(apk, "w") as package:
                package.writestr("AndroidManifest.xml", b"manifest")
                package.writestr("classes.dex", b"dex")
            self.assertEqual(inspect_package(apk)["adapter"], "waydroid")
            with zipfile.ZipFile(apk, "w") as package:
                package.writestr("readme.txt", "not an apk")
            self.assertEqual(inspect_package(apk)["status"], "rejected")

    def test_deb_requires_archive_signature_and_package_members(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, "app.deb", b"!<arch>\n")
            self.assertEqual(inspect_package(path)["status"], "rejected")
            def member(name, body):
                name_field = (name + "/").encode().ljust(16, b" ")
                header = (name_field + b"0".ljust(12) + b"0".ljust(6) + b"0".ljust(6)
                          + b"100644".ljust(8) + str(len(body)).encode().ljust(10) + b"`\n")
                return header + body + (b"\n" if len(body) & 1 else b"")
            path.write_bytes(b"!<arch>\n" + member("debian-binary", b"2.0\n")
                             + member("control.tar.xz", b"control") + member("data.tar.xz", b"data"))
            self.assertEqual(inspect_package(path)["format"], "deb")

    def test_crx_is_not_claimed_as_a_chromeos_native_application(self):
        with tempfile.TemporaryDirectory() as directory:
            result = inspect_package(self.write(directory, "addon.bin", b"Cr24\x03\x00\x00\x00payload"))
            self.assertEqual(result["format"], "chrome-extension")
            self.assertIn("no como aplicación ChromeOS", result["reason"])

    def test_mislabeled_unknown_file_is_never_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            result = inspect_package(self.write(directory, "setup.exe", b"hello world"))
            self.assertEqual(result["status"], "rejected")
            self.assertFalse(result["executed"])

    def test_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            real = self.write(directory, "real.exe", b"MZ")
            link = Path(directory) / "link.exe"
            link.symlink_to(real)
            self.assertEqual(inspect_package(link)["status"], "rejected")

    def test_missing_file_is_explained(self):
        with tempfile.TemporaryDirectory() as directory:
            result = inspect_package(Path(directory) / "missing.apk")
            self.assertEqual(result["status"], "unavailable")

    def test_dmg_requires_footer_signature(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, "disk.dmg", b"not a disk image")
            self.assertEqual(inspect_package(path)["status"], "rejected")
            path.write_bytes(b"disk image" + b"\0" * 498 + b"koly")
            self.assertEqual(inspect_package(path)["format"], "macos-dmg")


if __name__ == "__main__":
    unittest.main()
