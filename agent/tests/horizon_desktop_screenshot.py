"""Capture both running Nexus Horizon windows in the same virtual desktop."""
import importlib.util
import os
from pathlib import Path
from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[2]

def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

horizon = load("horizon_capture_launcher", "image/includes/opt/nexus/horizon.py")
panel = load("horizon_capture_panel", "image/includes/opt/nexus/horizon-panel.py")

bar = panel.HorizonPanel()
launcher = horizon.Horizon()
try:
    bar.geometry("1024x48+0+0")
    launcher.geometry("760x570+132+105")
    bar.update()
    launcher.update()
    launcher.lift()
    launcher.update()
    path = ROOT / "nexus-horizon-desktop-preview.png"
    ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).save(path)
    assert path.stat().st_size > 10000
    print(f"Captured real Horizon desktop integration: {path}")
finally:
    launcher.destroy()
    bar.destroy()
