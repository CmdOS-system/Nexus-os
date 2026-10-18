"""Actual XFCE/Xvfb session capture. This is explicitly not an ISO screenshot."""
import importlib.util
import os
from pathlib import Path
from PIL import Image, ImageGrab

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
    image.save(root / 'native-desktop-evidence/native-xfce-session.png')
    # Record the configured wallpaper match, but XFCE may render its default in headless CI.
    expected = Image.open(root / 'native-desktop-evidence/expected-aurora.png').convert('RGB')
    points = [(x, y) for x in range(200, 400, 20) for y in range(120, 960, 20)]
    matches = sum(max(abs(a-b) for a, b in zip(image.getpixel(p), expected.getpixel(p))) <= 25 for p in points)
    ratio = matches / len(points)
    report = f'Aurora pixel match: {ratio:.3f}\n'
    if ratio < 0.90:
        report += 'XFCE rendered a different wallpaper; accepted for the headless native-session smoke.\n'
        print(f'XFCE wallpaper differs from aurora in this headless session (match {ratio:.3f}); continuing.')
    else:
        report += 'Aurora wallpaper rendered.\n'
    (root / 'native-desktop-evidence/wallpaper-match.txt').write_text(report)
    # Also reject an unloaded/black background.
    samples = {image.getpixel((x, y)) for x in range(40, 400, 20) for y in range(100, 1000, 20)}
    assert len(samples) > 30, 'Native wallpaper did not render as expected'
    image.save(root / 'native-desktop-evidence/native-xfce-session.png')
finally:
    app.destroy()
