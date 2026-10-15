"""Linux process-level contention checks for Recovery G2."""
import multiprocessing
import tempfile
import unittest
from recovery_g2.boot_state import BootState
from recovery_g2.controller import RecoveryController

def attempt_boot(directory, queue):
    try:
        queue.put(RecoveryController(directory).prepare_boot())
    except Exception as exc:
        queue.put(type(exc).__name__)

class LockingTests(unittest.TestCase):
    def test_two_processes_consume_distinct_attempts(self):
        with tempfile.TemporaryDirectory() as directory:
            controller = RecoveryController(directory)
            controller.store.save(BootState())
            controller.stage_verified("B", authenticated=True, image_durable=True,
                                      attempts=1)
            context = multiprocessing.get_context("spawn")
            queue = context.Queue()
            processes = [context.Process(target=attempt_boot, args=(directory, queue))
                         for _ in range(2)]
            for process in processes:
                process.start()
            for process in processes:
                process.join(timeout=10)
                if process.is_alive():
                    process.terminate()
                    process.join()
                    self.fail("recovery lock deadlocked")
                self.assertEqual(process.exitcode, 0)
            self.assertEqual(sorted([queue.get(timeout=2), queue.get(timeout=2)]),
                             ["A", "B"])
            self.assertEqual(controller.store.load().confirmed, "A")
