import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from providers import AIProvider
from provider_diagnostics import test_provider_connection

class Good(AIProvider):
    def send(self,model,messages): return "OK"
class LeakyFailure(AIProvider):
    def send(self,model,messages): raise RuntimeError("Bearer super-secret-token")

class DiagnosticTests(unittest.TestCase):
    def test_success(self):
        self.assertEqual(test_provider_connection(Good(),"model"),(True,"Connected"))
    def test_error_does_not_leak_exception_message(self):
        ok,reason=test_provider_connection(LeakyFailure(),"model")
        self.assertFalse(ok)
        self.assertEqual(reason,"RuntimeError")
        self.assertNotIn("secret",reason)
    def test_model_required(self):
        with self.assertRaises(ValueError):
            test_provider_connection(Good(),"")
