"""Verify that the guest cannot close a scene before its exact screenshot ACK."""
import ast
import os
from pathlib import Path
import select
import sys
import threading
import time
import unittest
from unittest.mock import patch


def load_capture_ready():
    # The full guest probe performs Windows installations at module scope.
    # Load only its synchronization boundary to exercise real pipe I/O on Linux.
    root = Path(__file__).resolve().parents[2]
    path = root / 'image/windows-guest-probe.py'
    source = ast.parse(path.read_text())
    function = next(item for item in source.body
                    if isinstance(item, ast.FunctionDef) and item.name == 'capture_ready')
    namespace = {'select': select, 'sys': sys, 'time': time}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['capture_ready']


class CaptureSyncTests(unittest.TestCase):
    def test_scene_stays_open_until_its_own_ack(self):
        capture_ready = load_capture_ready()
        read_fd, write_fd = os.pipe()
        returned = threading.Event()
        pumping = threading.Event()
        errors = []

        class App:
            def update(self):
                pumping.set()

        with os.fdopen(read_fd) as incoming, os.fdopen(write_fd, 'w') as outgoing:
            def guest():
                try:
                    with patch.object(sys, 'stdin', incoming):
                        capture_ready(App(), 'SCENE', seconds=3)
                except Exception as error:
                    errors.append(error)
                finally:
                    returned.set()

            thread = threading.Thread(target=guest)
            thread.start()
            try:
                self.assertTrue(pumping.wait(1), 'Guest must keep pumping its UI')
                self.assertFalse(returned.is_set())
                outgoing.write('NEXUS_CAPTURE_ACK OTHER_SCENE\n')
                outgoing.flush()
                self.assertFalse(returned.wait(0.05), 'Another scene cannot release this one')
                outgoing.write('NEXUS_CAPTURE_ACK SCENE\n')
                outgoing.flush()
                self.assertTrue(returned.wait(1))
                self.assertEqual(errors, [])
            finally:
                thread.join(timeout=4)

    def test_missing_ack_is_a_failure(self):
        with self.assertRaisesRegex(RuntimeError, 'did not acknowledge'):
            load_capture_ready()(None, 'MISSING', seconds=0)


if __name__ == '__main__':
    unittest.main()
