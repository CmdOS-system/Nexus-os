#!/usr/bin/env python3
"""Show live user-mode runtime output in a small Cyber-Glass GTK window and capture it."""
import os
import sys
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk, GLib
from PIL import ImageGrab

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
window = Gtk.Window(title=title)
window.set_default_size(1280, 800)
window.set_position(Gtk.WindowPosition.CENTER)
outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
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
window.connect("destroy", Gtk.main_quit)

def capture():
    window.get_window().process_updates(True)
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    image = ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).convert("RGB")
    image.save(destination, "PNG")
    Gtk.main_quit()
    return GLib.SOURCE_REMOVE

window.show_all()
GLib.timeout_add(500, capture)
Gtk.main()
if Path(destination).stat().st_size < 4096:
    raise SystemExit("GTK screenshot is unexpectedly small")
print(f"Captured live GTK runtime output: {destination}")
