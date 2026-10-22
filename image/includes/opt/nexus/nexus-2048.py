#!/usr/bin/env python3
"""Interactive Nexus Cyber-Glass 2048 X11 recovery app."""
import random
import sys

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk


SIZE = 4
STYLE = b"""
window { background: #080d18; color: #edf7ff; font-family: 'Noto Sans', sans-serif; }
.shell { background-image: linear-gradient(145deg,#111c2d,#090f1b); border: 1px solid #176579; border-radius: 20px; padding: 16px; }
.brand { color: #6df5ff; font-size: 22px; font-weight: bold; }
.muted { color: #9db1c8; }
.tile { background: #15283b; color: #effcff; border: 1px solid #24637a; border-radius: 12px; font-size: 28px; font-weight: bold; }
.tile-hot { background-image: linear-gradient(135deg,#075d70,#3f3480); color: white; border: 1px solid #52ebf0; border-radius: 12px; font-size: 28px; font-weight: bold; }
button { background: #142235; color: #e9faff; border: 1px solid #28566b; border-radius: 9px; padding: 7px 12px; }
"""


class Game:
    def __init__(self, title="2048"):
        self.score = 0
        self.board = [[0] * SIZE for _ in range(SIZE)]
        self.window = Gtk.Window(title=title)
        self.window.set_default_size(780, 560)
        self.window.set_position(Gtk.WindowPosition.NONE)
        self.window.move(700, 76)
        self.window.set_type_hint(Gdk.WindowTypeHint.NORMAL)
        self.window.connect("key-press-event", self.key_press)
        self.window.connect("destroy", Gtk.main_quit)
        provider = Gtk.CssProvider()
        provider.load_from_data(STYLE)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        shell.get_style_context().add_class("shell")
        shell.set_margin_top(12); shell.set_margin_bottom(12)
        shell.set_margin_start(12); shell.set_margin_end(12)
        self.window.add(shell)
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        shell.pack_start(header, False, False, 0)
        brand = Gtk.Label(label="NEXUS  /  2048")
        brand.get_style_context().add_class("brand")
        brand.set_xalign(0)
        header.pack_start(brand, True, True, 0)
        self.score_label = Gtk.Label()
        header.pack_start(self.score_label, False, False, 0)
        restart = Gtk.Button(label="Nuevo juego")
        restart.connect("clicked", self.reset)
        header.pack_end(restart, False, False, 0)
        hint = Gtk.Label(label="Usa ← ↑ → ↓ o W A S D para mover las fichas")
        hint.get_style_context().add_class("muted")
        hint.set_xalign(0)
        shell.pack_start(hint, False, False, 0)
        self.grid = Gtk.Grid(row_spacing=8, column_spacing=8)
        self.grid.set_halign(Gtk.Align.CENTER)
        self.grid.set_valign(Gtk.Align.CENTER)
        self.grid.set_hexpand(True); self.grid.set_vexpand(True)
        shell.pack_start(self.grid, True, True, 0)
        self.add_tile(); self.add_tile(); self.render()
        self.window.show_all()
        self.window.present()

    def reset(self, *_):
        self.score = 0
        self.board = [[0] * SIZE for _ in range(SIZE)]
        self.add_tile(); self.add_tile(); self.render()

    def add_tile(self):
        empty = [(y, x) for y in range(SIZE) for x in range(SIZE) if not self.board[y][x]]
        if empty:
            y, x = random.choice(empty)
            self.board[y][x] = 4 if random.random() < 0.1 else 2

    def key_press(self, _widget, event):
        key = Gdk.keyval_name(event.keyval).lower()
        directions = {"left": "left", "a": "left", "right": "right", "d": "right",
                      "up": "up", "w": "up", "down": "down", "s": "down"}
        direction = directions.get(key)
        if direction:
            self.move(direction)
            return True
        return False

    def move(self, direction):
        before = [row[:] for row in self.board]
        for index in range(SIZE):
            coords = [(index, n) for n in range(SIZE)] if direction in ("left", "right") else [(n, index) for n in range(SIZE)]
            if direction in ("right", "down"):
                coords.reverse()
            values = [self.board[y][x] for y, x in coords if self.board[y][x]]
            merged = []
            pos = 0
            while pos < len(values):
                if pos + 1 < len(values) and values[pos] == values[pos + 1]:
                    value = values[pos] * 2; self.score += value
                    merged.append(value); pos += 2
                else:
                    merged.append(values[pos]); pos += 1
            merged.extend([0] * (SIZE - len(merged)))
            for (y, x), value in zip(coords, merged):
                self.board[y][x] = value
        if before != self.board:
            self.add_tile()
        self.render()

    def render(self):
        for child in self.grid.get_children():
            self.grid.remove(child)
        self.score_label.set_text(f"PUNTAJE  {self.score}")
        for y, row in enumerate(self.board):
            for x, value in enumerate(row):
                cell = Gtk.Label(label=str(value) if value else "")
                cell.set_size_request(112, 92)
                cell.get_style_context().add_class("tile-hot" if value >= 32 else "tile")
                self.grid.attach(cell, x, y, 1, 1)
        self.grid.show_all()


class MinesGame:
    def __init__(self):
        self.window = Gtk.Window(title="GNOME Mines")
        self.window.set_default_size(780, 560)
        self.window.set_position(Gtk.WindowPosition.NONE); self.window.move(700, 76)
        self.window.connect("destroy", Gtk.main_quit)
        provider = Gtk.CssProvider(); provider.load_from_data(STYLE)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        shell.get_style_context().add_class("shell")
        shell.set_margin_top(12); shell.set_margin_bottom(12)
        shell.set_margin_start(12); shell.set_margin_end(12)
        self.window.add(shell)
        brand = Gtk.Label(label="NEXUS  /  GNOME MINES")
        brand.get_style_context().add_class("brand"); brand.set_xalign(0)
        shell.pack_start(brand, False, False, 0)
        self.status = Gtk.Label(label="Revela las celdas; evita las minas.")
        self.status.set_xalign(0); self.status.get_style_context().add_class("muted")
        shell.pack_start(self.status, False, False, 0)
        self.grid = Gtk.Grid(row_spacing=3, column_spacing=3)
        self.grid.set_halign(Gtk.Align.CENTER); self.grid.set_valign(Gtk.Align.CENTER)
        self.grid.set_hexpand(True); self.grid.set_vexpand(True)
        shell.pack_start(self.grid, True, True, 0)
        self.reset(); self.window.show_all(); self.window.present()

    def reset(self, *_):
        self.mines = set(random.sample(range(81), 10)); self.done = False
        for child in self.grid.get_children(): self.grid.remove(child)
        for index in range(81):
            button = Gtk.Button(label="•"); button.set_size_request(45, 40)
            button.connect("clicked", self.reveal, index)
            self.grid.attach(button, index % 9, index // 9, 1, 1)
        self.grid.show_all(); self.status.set_text("Revela las celdas; evita las minas.")

    def reveal(self, button, index):
        if self.done: return
        if index in self.mines:
            button.set_label("✹"); self.status.set_text("¡Mina! Pulsa para empezar otra partida.")
            self.done = True
            for child in self.grid.get_children():
                child.set_sensitive(False)
            return
        row, col = divmod(index, 9)
        count = sum((r * 9 + c) in self.mines for r in range(max(0,row-1),min(9,row+2))
                    for c in range(max(0,col-1),min(9,col+2)))
        button.set_label(str(count) if count else " "); button.set_sensitive(False)
        self.status.set_text("¡Bien! Sigue explorando el tablero.")


if __name__ == "__main__":
    title = sys.argv[1] if len(sys.argv) > 1 else "2048"
    if "mines" in title.casefold(): MinesGame()
    else: Game(title)
    Gtk.main()
