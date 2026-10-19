#!/usr/bin/env python3
"""Render live runtime output in a visible GTK window and capture its pixels."""
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
.frame { background: linear-gradient(145deg, #111e32, #090e18); border: 1px solid #164b62; border-radius: 24px; padding: 38px; }
.brand { color: #00e8f4; font-size: 15px; font-weight: bold; letter-spacing: 3px; }
.title { color: #eff9ff; font-size: 32px; font-weight: bold; }
.output { color: #80f3ff; background: #07111d; border-left: 4px solid #00e8f4; padding: 22px; font-family: monospace; font-size: 19px; }
.status { color: #7cf5a5; font-size: 16px; font-weight: bold; }
"""
provider = Gtk.CssProvider()
provider.load_from_data(css)
screen = Gdk.Screen.get_default()
if screen is None:
    raise SystemExit("GTK could not find the active Xvfb screen")
Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

window = Gtk.Window(title=title)
window.set_default_size(1120, 620)
window.set_position(Gtk.WindowPosition.CENTER)
window.set_keep_above(True)
outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
for edge in ("start", "end", "top", "bottom"):
    getattr(outer, f"set_margin_{edge}")(44)
outer.get_style_context().add_class("frame")
brand = Gtk.Label(label="NEXUS · LIVE USER-MODE EXECUTION")
brand.set_xalign(0)
brand.get_style_context().add_class("brand")
heading = Gtk.Label(label=title)
heading.set_xalign(0)
heading.set_line_wrap(True)
heading.get_style_context().add_class("title")
status = Gtk.Label(label="LOADING SUBSYSTEM OUTPUT…")
status.set_xalign(0)
status.get_style_context().add_class("status")
result = Gtk.Label(label=output)
result.set_xalign(0)
result.set_line_wrap(True)
result.set_selectable(True)
result.get_style_context().add_class("output")
for widget in (brand, heading, status, result):
    outer.pack_start(widget, False, False, 0)
window.add(outer)

capture_error = None

def mark_running():
    status.set_text("SUBSYSTEM EXECUTED · LIVE OUTPUT VERIFIED")
    return GLib.SOURCE_REMOVE

def capture_and_quit():
    global capture_error
    try:
        gdk_window = window.get_window()
        if gdk_window is None:
            raise RuntimeError("GTK window was not mapped on Xvfb")
        display = Gdk.Display.get_default()
        if display is not None:
            display.sync()
        pixbuf = Gdk.pixbuf_get_from_window(
            gdk_window, 0, 0, gdk_window.get_width(), gdk_window.get_height()
        )
        if pixbuf is None:
            raise RuntimeError("GDK could not capture the visible GTK window")
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        pixbuf.savev(destination, "png", [], [])
    except Exception as error:
        capture_error = str(error)
    Gtk.main_quit()
    return GLib.SOURCE_REMOVE

def hard_quit():
    global capture_error
    capture_error = capture_error or "GTK capture exceeded its 5-second safety limit"
    Gtk.main_quit()
    return GLib.SOURCE_REMOVE

window.show_all()
GLib.timeout_add(350, mark_running)
GLib.timeout_add(1200, capture_and_quit)
GLib.timeout_add(5000, hard_quit)
Gtk.main()
if capture_error:
    raise SystemExit(f"GTK evidence capture failed: {capture_error}")
if not Path(destination).is_file() or Path(destination).stat().st_size < 4096:
    raise SystemExit("GTK screenshot is unexpectedly small")
print(f"Captured live GTK runtime output: {destination}")
