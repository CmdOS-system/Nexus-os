import unittest
from recovery_g2.qemu_preflight import preflight, OVMF_CANDIDATES

class QemuPreflightTests(unittest.TestCase):
    def test_missing_prerequisites(self):
        result = preflight(which=lambda name: None, exists=lambda path: False)
        self.assertFalse(result["ready_for_vm_setup"])
        self.assertIsNone(result["ovmf_code"])

    def test_detects_qemu_and_firmware(self):
        code, vars_ = OVMF_CANDIDATES[0]
        result = preflight(which=lambda name: "/usr/bin/" + name,
                           exists=lambda path: path in (code, vars_))
        self.assertTrue(result["ready_for_vm_setup"])
        self.assertEqual(result["ovmf_code"], code)
        self.assertEqual(result["ovmf_vars_template"], vars_)

    def test_firmware_requires_code_and_vars(self):
        result = preflight(which=lambda name: "/usr/bin/" + name,
                           exists=lambda path: path.endswith("CODE_4M.fd"))
        self.assertFalse(result["ready_for_vm_setup"])
