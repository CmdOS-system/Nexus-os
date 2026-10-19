#!/usr/bin/env python3
"""Small GTK response surface for Nexus OmniSubsystem."""
import argparse
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

CSS = """
window, .root { background-color: rgba(11, 15, 25, 0.96); color: #edf7ff; font-family: Inter, "Noto Sans", sans-serif; }
.root { border: 1px solid #00F0FF; border-radius: 18px; }
.eyebrow { color: #00F0FF; font-size: 10pt; font-weight: 700; letter-spacing: 1px; }
.badge { background-color: rgba(0, 240, 255, 0.12); color: #70f5ff; border: 1px solid #00F0FF; border-radius: 12px; padding: 5px 11px; font-weight: 700; }
.title { color: #f5fbff; font-size: 20pt; font-weight: 700; }
.copy { color: #c4d1e1; font-size: 11pt; }
.detail { color: #9fb4c9; font-size: 9pt; }
button { background-image: none; background-color: rgba(20, 30, 48, 0.94); color: #edf7ff; border: 1px solid #30445e; border-radius: 10px; padding: 9px 18px; }
button:hover { background-color: rgba(0, 240, 255, 0.12); border-color: #00F0FF; }
button.primary { background-color: #00dbea; color: #07121d; border-color: #00F0FF; font-weight: 700; }
button.primary:hover { background-color: #70f5ff; }
"""


class NexusDialog:
    def __init__(self, args):
        self.result = 1 if args.question else 0
        self.window = Gtk.Window(title=args.title)
        self.window.set_default_size(570, 390 if args.path else 340)
        self.window.set_resizable(False)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("delete-event", self._closed)
        self.window.connect("destroy", lambda *_: Gtk.main_quit())
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.window.set_visual(visual)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        shell.get_style_context().add_class("root")
        shell.set_margin_top(22)
        shell.set_margin_bottom(20)
        shell.set_margin_start(24)
        shell.set_margin_end(24)
        self.window.add(shell)

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        badge = Gtk.Label(label="◈  " + args.ecosystem.upper())
        badge.get_style_context().add_class("badge")
        bar.pack_start(badge, False, False, 0)
        eyebrow = Gtk.Label(label="NEXUS  /  OMNISUBSYSTEM")
        eyebrow.get_style_context().add_class("eyebrow")
        eyebrow.set_xalign(0)
        bar.pack_start(eyebrow, True, True, 0)
        close = Gtk.Button(label="×")
        close.connect("clicked", lambda *_: self.window.destroy())
        bar.pack_end(close, False, False, 0)
        shell.pack_start(bar, False, False, 0)

        title = Gtk.Label(label=args.title)
        title.get_style_context().add_class("title")
        title.set_xalign(0)
        title.set_line_wrap(True)
        shell.pack_start(title, False, False, 0)
        message = Gtk.Label(label=args.message)
        message.get_style_context().add_class("copy")
        message.set_xalign(0)
        message.set_yalign(0)
        message.set_line_wrap(True)
        message.set_max_width_chars(68)
        shell.pack_start(message, True, True, 0)
        if args.path:
            detail = Gtk.Label(label=args.path)
            detail.get_style_context().add_class("detail")
            detail.set_xalign(0)
            detail.set_line_wrap(True)
            shell.pack_start(detail, False, False, 0)

        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        footer.set_halign(Gtk.Align.END)
        if args.question:
            cancel = Gtk.Button(label="Cancelar")
            cancel.connect("clicked", lambda *_: self.window.destroy())
            footer.pack_start(cancel, False, False, 0)
            proceed = Gtk.Button(label=args.accept_label)
            proceed.get_style_context().add_class("primary")
            proceed.connect("clicked", self._accept)
            footer.pack_start(proceed, False, False, 0)
        else:
            close = Gtk.Button(label="Listo")
            close.get_style_context().add_class("primary")
            close.connect("clicked", lambda *_: self.window.destroy())
            footer.pack_start(close, False, False, 0)
        shell.pack_end(footer, False, False, 0)

    def _closed(self, *_):
        Gtk.main_quit()
        return False

    def _accept(self, *_):
        self.result = 0
        self.window.destroy()

    def run(self):
        self.window.show_all()
        Gtk.main()
        return self.result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ecosystem", default="Nexus")
    parser.add_argument("--title", default="Nexus OmniSubsystem")
    parser.add_argument("--message", default="")
    parser.add_argument("--path", default="")
    parser.add_argument("--question", action="store_true")
    parser.add_argument("--accept-label", default="Continuar")
    args = parser.parse_args()
    return NexusDialog(args).run()


if __name__ == "__main__":
    raise SystemExit(main())
