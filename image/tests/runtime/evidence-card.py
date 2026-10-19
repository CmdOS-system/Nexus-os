#!/usr/bin/env python3
"""Show live user-mode runtime output in a small Cyber-Glass GTK window and capture it."""
import sys
from pathlib import Path

import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk, GLib

if len(sys.argv) != 4:
    raise SystemExit("usage: evidence-card.py TITLE OUTPUT DESTINATION")
title, output, destination = sys.argv[1:]

css = b"""
window { background: #080d18; color: #eff9ff; }
.frame { background: linear-gradient(145deg, #111e32, #090e18); border: 1px solid #164b62; border-radius: 24px; padding: 42px; }
.brand { color: #00e8f4; font-size: 15px; font-weight: bold; letter-spacing: 3px; }
.title { color: #eff9ff; font-size: 32px; font-weight: bold; }
.output { color: #80f3ff; background: #07111d; border-left: 4px solid #00e8f4; padding: 22px; font-family: monospace; font-size: 19px; }
"""
provider = Gtk.CssProvider()
provider.load_from_data(css)
screen = Gdk.Screen.get_default()
if screen is None:
    raise SystemExit("GTK could not find the active display screen")
Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
window = Gtk.OffscreenWindow()
outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
outer.set_size_request(1280, 800)
outer.set_halign(Gtk.Align.CENTER)
outer.set_valign(Gtk.Align.CENTER)
outer.set_margin_start(90)
outer.set_margin_end(90)
outer.set_margin_top(60)
outer.set_margin_bottom(60)
outer.get_style_context().add_class("frame")
brand = Gtk.Label(label="NEXUS · LIVE USER-MODE EXECUTION")
brand.set_xalign(0)
brand.get_style_context().add_class("brand")
heading = Gtk.Label(label=title)
heading.set_xalign(0)
heading.set_line_wrap(True)
heading.get_style_context().add_class("title")
caption = Gtk.Label(label="Salida capturada del payload ejecutado en vivo")
caption.set_xalign(0)
result = Gtk.Label(label=output)
result.set_xalign(0)
result.set_line_wrap(True)
result.set_selectable(True)
result.get_style_context().add_class("output")
for widget in (brand, heading, caption, result):
    widget.set_margin_bottom(18)
    outer.pack_start(widget, False, False, 0)
window.add(outer)

capture_error = None

def capture_snapshot(widget, _event):
    global capture_error
    try:
        pixbuf = widget.get_pixbuf()
        if pixbuf is None:
            return False
        if pixbuf.get_width() < 200 or pixbuf.get_height() < 100:
            raise RuntimeError(f"GTK rendered an undersized snapshot: {pixbuf.get_width()}x{pixbuf.get_height()}")
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        pixbuf.savev(destination, "png", [], [])
    except Exception as error:
        capture_error = str(error)
    Gtk.main_quit()
    return False

def capture_timeout():
    global capture_error
    capture_error = "GTK offscreen renderer did not emit a draw event within 5 seconds"
    Gtk.main_quit()
    return GLib.SOURCE_REMOVE

window.connect("damage-event", capture_snapshot)
GLib.timeout_add_seconds(5, capture_timeout)
window.show_all()
Gtk.main()
if capture_error:
    raise SystemExit(f"GTK evidence capture failed: {capture_error}")
if not Path(destination).is_file() or Path(destination).stat().st_size < 4096:
    raise SystemExit("GTK screenshot is unexpectedly small")
print(f"Captured live GTK runtime output: {destination}")
