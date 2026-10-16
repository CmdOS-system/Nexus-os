"""Offline tests for the loopback-only model readiness probe."""
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_model_diagnostics import check_local_model, OLLAMA_TAGS_URL, _NoRedirect, _open_local_tags
from urllib.request import ProxyHandler

class Response:
    status = 200
    def __init__(self, payload):
        self.data = io.BytesIO(payload)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.data.close()
    def read(self, n):
        return self.data.read(n)

class LocalModelTests(unittest.TestCase):
    @patch("local_model_diagnostics._open_local_tags")
    def test_installed_model(self, opener):
        opener.return_value = Response(json.dumps({"models":[{"name":"llama3:latest"}]}).encode())
        self.assertEqual(check_local_model("llama3"), (True, "Local model is installed and the service responded."))
        opener.assert_called_once_with(2.0)

    @patch("local_model_diagnostics._open_local_tags")
    def test_missing_model(self, opener):
        opener.return_value = Response(b'{"models":[]}')
        self.assertFalse(check_local_model("missing")[0])

    @patch("local_model_diagnostics._open_local_tags", side_effect=OSError("secret-bearing exception"))
    def test_network_error_is_sanitized(self, opener):
        result = check_local_model("llama3")
        self.assertFalse(result[0])
        self.assertNotIn("secret", result[1])

    def test_empty_model_does_not_connect(self):
        with patch("local_model_diagnostics._open_local_tags") as opener:
            self.assertFalse(check_local_model(" ")[0])
            opener.assert_not_called()

    def test_redirect_is_blocked(self):
        self.assertIsNone(_NoRedirect().redirect_request(None, None, 302, "Found", {}, "https://example.org"))

    @patch("local_model_diagnostics.build_opener")
    def test_local_probe_uses_redirect_blocking_handler(self, build):
        _open_local_tags(2.0)
        handlers = build.call_args.args
        self.assertIsInstance(handlers[0], ProxyHandler)
        self.assertEqual(handlers[0].proxies, {})
        self.assertIs(handlers[1], _NoRedirect)
        build.return_value.open.assert_called_once_with(OLLAMA_TAGS_URL, timeout=2.0)

    def test_rejects_excessive_timeout(self):
        with self.assertRaises(ValueError):
            check_local_model("llama3", timeout=100)
