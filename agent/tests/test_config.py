import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import ProviderConfig

class ConfigTests(unittest.TestCase):
    def test_local_config(self):
        c = ProviderConfig("ollama", "ollama", local=True, models=("model-a",))
        self.assertIs(c.validate(), c)

    def test_cloud_secret_reference(self):
        c = ProviderConfig("cloud", "compatible", secret_ref="keyring:nexus/cloud")
        self.assertIs(c.validate(), c)

    def test_reject_plain_secret(self):
        with self.assertRaises(ValueError):
            ProviderConfig("cloud", "compatible", secret_ref="sk-example").validate()

    def test_reject_local_secret(self):
        with self.assertRaises(ValueError):
            ProviderConfig("local", "ollama", local=True, secret_ref="keyring:x").validate()

    def test_reject_empty_model(self):
        with self.assertRaises(ValueError):
            ProviderConfig("cloud", "compatible", models=("",)).validate()
