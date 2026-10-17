"""Run the real Nexus Horizon window on a virtual X display."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2] / "image/includes/opt/nexus/horizon.py"
spec = importlib.util.spec_from_file_location("nexus_horizon_gui", SOURCE)
horizon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(horizon)

class HorizonSmoke(unittest.TestCase):
    def setUp(self):
        self.app = horizon.Horizon()
        self.app.update_idletasks()

    def tearDown(self):
        self.app.destroy()

    def test_window_search_and_keyboard_launch(self):
        self.assertEqual(self.app.title(), "Nexus Horizon")
        self.app.search.set("control")
        self.app.update_idletasks()
        self.assertEqual(len(self.app.list_frame.winfo_children()), 1)
        with patch.object(horizon, "launch") as launch:
            self.app.launch_first()
        launch.assert_called_once_with(("/usr/bin/python3", "/opt/nexus/control-center.py"))

    def test_unknown_search_does_not_launch(self):
        self.app.search.set("no-such-nexus-app")
        with patch.object(horizon, "launch") as launch:
            self.app.launch_first()
        launch.assert_not_called()

    def test_launch_error_is_handled(self):
        with patch.object(horizon, "launch", side_effect=FileNotFoundError):
            self.app.open_app(("missing-command",))
        self.assertIn("unavailable", self.app.feedback.get())

    def test_keyboard_opens_focused_card_instead_of_first_result(self):
        self.app.update()
        self.app._app_buttons[3].focus_force()
        self.app.update()
        with patch.object(horizon, "launch") as launch:
            self.app.launch_first()
        launch.assert_called_once_with(("xfce4-settings-manager",))

    def test_small_window_keeps_last_application_reachable(self):
        self.app.geometry("560x460")
        self.app.update()
        self.app.scroll.yview_moveto(1)
        self.app.update()
        last = self.app._app_buttons[-1]
        self.assertGreater(last.winfo_rooty() + last.winfo_height(), self.app.scroll.winfo_rooty())
        self.assertLessEqual(last.winfo_rooty(), self.app.scroll.winfo_rooty() + self.app.scroll.winfo_height())
        for card in self.app.list_frame.winfo_children():
            self.assertLessEqual(card.winfo_x() + card.winfo_width(), self.app.list_frame.winfo_width())

if __name__ == "__main__":
    unittest.main()
