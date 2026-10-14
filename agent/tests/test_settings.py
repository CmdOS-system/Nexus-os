import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from settings import AISettings

class SettingsTests(unittest.TestCase):
    def test_off_by_default(self):
        self.assertEqual(AISettings().validate().mode, "off")

    def test_local(self):
        s = AISettings("local", "ollama", "model-a")
        self.assertEqual(AISettings.from_json(s.to_json()), s)

    def test_cloud_requires_consent(self):
        with self.assertRaises(ValueError):
            AISettings("cloud", "compatible", "model-a").validate()

    def test_cloud_with_consent(self):
        self.assertTrue(AISettings("cloud", "compatible", "model-a", True).validate().cloud_consent)

    def test_local_rejects_cloud_consent(self):
        with self.assertRaises(ValueError):
            AISettings("local", "ollama", "model-a", True).validate()

    def test_unknown_fields_rejected(self):
        with self.assertRaises(ValueError):
            AISettings.from_json('{"mode":"off","provider":null,"model":null,"cloud_consent":false,"api_key":"secret"}')
