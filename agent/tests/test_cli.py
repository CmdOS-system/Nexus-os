import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cli

class CLITests(unittest.TestCase):
    def test_local_chat_and_exit(self):
        with patch.object(sys, "argv", ["cli", "--model", "test-model"]), \
             patch("builtins.input", side_effect=["hello", "/exit"]), \
             patch("cli.chat", return_value="response") as fake, \
             patch("sys.stdout", new_callable=io.StringIO) as output:
            cli.main()
            self.assertIn("response", output.getvalue())
            fake.assert_called_once()

    def test_invalid_remote_endpoint(self):
        with patch.object(sys, "argv", ["cli", "--model", "test-model", "--endpoint", "http://example.org"]):
            with self.assertRaises(ValueError):
                cli.main()
