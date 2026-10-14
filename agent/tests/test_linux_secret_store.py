import sys
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from linux_secret_store import LinuxSecretStore

class LinuxSecretStoreTests(unittest.TestCase):
    @patch("linux_secret_store.shutil.which", return_value="/usr/bin/secret-tool")
    @patch("linux_secret_store.subprocess.run")
    def test_store_uses_stdin_not_command_line(self, run, which):
        run.return_value = Mock(returncode=0, stdout="")
        s = LinuxSecretStore()
        s.store("keyring:nexus/openai", "example-secret")
        args, kwargs = run.call_args
        self.assertNotIn("example-secret", args[0])
        self.assertEqual(kwargs["input"], "example-secret\n")

    @patch("linux_secret_store.shutil.which", return_value="/usr/bin/secret-tool")
    @patch("linux_secret_store.subprocess.run")
    def test_resolve(self, run, which):
        run.return_value = Mock(returncode=0, stdout="token-value\n")
        self.assertEqual(LinuxSecretStore().resolve("keyring:nexus/provider"), "token-value")

    @patch("linux_secret_store.shutil.which", return_value=None)
    def test_missing_service_fails_closed(self, which):
        with self.assertRaises(RuntimeError):
            LinuxSecretStore().resolve("keyring:nexus/openai")

    def test_invalid_reference_rejected(self):
        with self.assertRaises(ValueError):
            LinuxSecretStore().resolve("keyring:other/provider")

    @patch("linux_secret_store.shutil.which", return_value="/usr/bin/secret-tool")
    @patch("linux_secret_store.subprocess.run")
    def test_service_error_is_not_silent(self, run, which):
        run.return_value = Mock(returncode=1, stdout="", stderr="private error")
        with self.assertRaises(RuntimeError):
            LinuxSecretStore().resolve("keyring:nexus/openai")
