"""Capture the real Nexus Horizon Tk window on Xvfb for visual review.

This is a screenshot of a running GUI, not an illustrative mockup.
"""
import importlib.util
import os
from pathlib import Path
from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "image/includes/opt/nexus/horizon.py"
spec = importlib.util.spec_from_file_location("nexus_horizon_capture", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

app = module.Horizon()
try:
    app.geometry("1040x820+440+130")
    app.update()
    app.after(500, app.quit)
    app.mainloop()
    app.update()
    app.focus_force()
    app.update()
    output = ROOT / "nexus-horizon-preview.png"
    bounds = (app.winfo_rootx(), app.winfo_rooty(),
              app.winfo_rootx() + app.winfo_width(), app.winfo_rooty() + app.winfo_height())
    ImageGrab.grab(bbox=bounds, xdisplay=os.environ["DISPLAY"]).save(output)
    assert output.stat().st_size > 10000, "Screenshot is unexpectedly small"
    print(f"Horizon screenshot captured: {output} ({output.stat().st_size} bytes)")
finally:
    app.destroy()
