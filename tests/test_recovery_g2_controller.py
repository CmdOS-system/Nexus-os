import tempfile
import unittest
from recovery_g2.boot_state import BootState
from recovery_g2.controller import RecoveryController

class ControllerTests(unittest.TestCase):
    def test_rejects_unverified_image(self):
        with tempfile.TemporaryDirectory() as directory:
            controller = RecoveryController(directory)
            controller.store.save(BootState())
            with self.assertRaises(ValueError):
                controller.stage_verified("B", authenticated=False, image_durable=True)
            self.assertEqual(controller.store.load(), BootState())

    def test_restarts_and_automatic_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            controller = RecoveryController(directory)
            controller.store.save(BootState())
            controller.stage_verified("B", authenticated=True, image_durable=True, attempts=2)
            self.assertEqual(RecoveryController(directory).prepare_boot(), "B")
            self.assertEqual(RecoveryController(directory).prepare_boot(), "B")
            self.assertEqual(RecoveryController(directory).prepare_boot(), "A")

    def test_confirmation_after_last_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            controller = RecoveryController(directory)
            controller.store.save(BootState())
            controller.stage_verified("B", authenticated=True, image_durable=True, attempts=1)
            self.assertEqual(controller.prepare_boot(), "B")
            controller.confirm_health("B", healthy=True)
            self.assertEqual(RecoveryController(directory).prepare_boot(), "B")

    def test_cancel_pending_update(self):
        with tempfile.TemporaryDirectory() as directory:
            controller = RecoveryController(directory)
            controller.store.save(BootState())
            controller.stage_verified("B", authenticated=True, image_durable=True)
            controller.cancel_update()
            self.assertEqual(controller.prepare_boot(), "A")
