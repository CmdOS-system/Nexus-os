#!/usr/bin/env python3
"""Display original APK artwork in a bounded desktop window for CI evidence."""
import hashlib
import json
import sys
import zipfile
from io import BytesIO
from pathlib import Path

from PIL import Image

if len(sys.argv) != 3:
    raise SystemExit("usage: android-resource-fallback.py REAL.apk OUTPUT_DIR")
apk_path = Path(sys.argv[1]).resolve()
output_dir = Path(sys.argv[2]).resolve()
output_dir.mkdir(parents=True, exist_ok=True)
resources = []
seen = set()
with zipfile.ZipFile(apk_path) as apk:
    for name in apk.namelist():
        if not name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue
        if not (name.startswith("res/drawable") or name.startswith("res/mipmap") or name.startswith("assets/")):
            continue
        raw = apk.read(name)
        try:
            with Image.open(BytesIO(raw)) as original:
                if original.width < 48 or original.height < 48:
                    continue
                image = original.convert("RGBA")
                fingerprint = hashlib.sha256(image.tobytes()).hexdigest()
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                image.thumbnail((280, 180), Image.Resampling.LANCZOS)
                output = output_dir / f"apk-resource-{len(resources) + 1}.png"
                image.save(output, "PNG")
        except (OSError, ValueError):
            continue
        resources.append({"member": name, "source_sha256": hashlib.sha256(raw).hexdigest(),
                          "output": output.name,
                          "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
        if len(resources) == 6:
            break
if not resources:
    raise SystemExit("The real 2048 APK contains no usable graphic resources")
manifest = {"apk": str(apk_path), "apk_sha256": hashlib.sha256(apk_path.read_bytes()).hexdigest(),
            "resources": resources}
(output_dir / "apk-resource-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf

css = Gtk.CssProvider()
css.load_from_data(b"""
window.cyber-glass { background-color: #071421; border: 2px solid #43e7ff; }
.cyber-panel { background-color: #10283a; border: 1px solid #38c8e8; border-radius: 12px; }
.cyber-title { color: #ecfbff; font-size: 24px; font-weight: bold; }
.cyber-subtitle { color: #8bb6c8; font-size: 12px; }
.cyber-caption { color: #8deaff; font-size: 11px; }
""")
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css,
                                         Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
window = Gtk.Window(title="2048")
window.set_wmclass("nexus-apk-resource-fallback", "NexusApkResourceFallback")
window.set_default_size(780, 560)
window.set_resizable(False)
window.set_position(Gtk.WindowPosition.CENTER)
window.get_style_context().add_class("cyber-glass")
outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
outer.set_border_width(22)
header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
heading = Gtk.Label(label="2048")
heading.get_style_context().add_class("cyber-title")
subtitle = Gtk.Label(label="Android APK • recursos gráficos originales")
subtitle.get_style_context().add_class("cyber-subtitle")
header.pack_start(heading, False, False, 0)
header.pack_start(subtitle, False, False, 0)
outer.pack_start(header, False, False, 0)
panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
panel.set_border_width(18)
panel.get_style_context().add_class("cyber-panel")
grid = Gtk.Grid(column_spacing=12, row_spacing=12)
for index, resource in enumerate(resources):
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(output_dir / resource["output"]))
    card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    card.pack_start(Gtk.Image.new_from_pixbuf(pixbuf), True, True, 0)
    caption = Gtk.Label(label=f"APK drawable {index + 1}")
    caption.get_style_context().add_class("cyber-caption")
    card.pack_start(caption, False, False, 0)
    grid.attach(card, index % 3, index // 3, 1, 1)
panel.pack_start(grid, True, True, 0)
outer.pack_start(panel, True, True, 0)
window.add(outer)
window.connect("destroy", Gtk.main_quit)
window.show_all()
Gtk.main()
