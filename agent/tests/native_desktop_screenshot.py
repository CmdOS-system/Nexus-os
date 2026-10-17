"""Actual XFCE/Xvfb session capture. This is explicitly not an ISO screenshot."""
import importlib.util
import os
from pathlib import Path
from PIL import ImageGrab

root = Path(__file__).resolve().parents[2]
source = root / 'image/includes/opt/nexus/horizon.py'
spec = importlib.util.spec_from_file_location('native_horizon', source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = module.Horizon()
try:
    app.geometry('1040x820+440+130')
    app.update()
    app.after(1500, app.quit)
    app.mainloop()
    app.update()
    image = ImageGrab.grab(xdisplay=os.environ['DISPLAY']).convert('RGB')
    assert image.size == (1920, 1080), image.size
    # Sample the desktop, outside the launcher, to reject an unloaded/black background.
    samples = {image.getpixel((x, y)) for x in range(40, 400, 20) for y in range(100, 1000, 20)}
    assert len(samples) > 30, 'Native wallpaper did not render as expected'
    image.save(root / 'native-desktop-evidence/native-xfce-session.png')
finally:
    app.destroy()
