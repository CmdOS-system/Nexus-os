#!/usr/bin/env python3
"""Nexus OmniStore: curated storefront directory and safe package handoff UI."""
import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import re
import time
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk
from omni_store_sources import SourceStore


HOME = Path.home()
STATE = HOME / ".local/share/nexus/omnistore-installed.json"
MIN_INSTALL_STATE_SECONDS = 2.8
CSS = """
window { background-color: rgba(5,7,13,0.84); color: #F3F7FF; font-family: Inter, 'Noto Sans', sans-serif; }
.shell { background-color: transparent; }
.sidebar { background-image: linear-gradient(155deg, rgba(18,27,43,0.78), rgba(8,13,24,0.82)); border: 1px solid rgba(255,255,255,0.08); border-radius: 22px; box-shadow: 0 18px 48px rgba(0,0,0,0.38); }
.brand { color: #F8FBFF; font-size: 20pt; font-weight: 800; letter-spacing: 0.5px; }
.brand-accent { color: #00F2FF; }
.eyebrow { color: #74EAF2; font-size: 8pt; font-weight: 700; letter-spacing: 1.6px; }
.headline { color: #F7FAFF; font-size: 27pt; font-weight: 700; }
.muted { color: rgba(218,229,245,0.62); }
.nav-button { background-color: transparent; color: rgba(226,235,250,0.68); border: 1px solid transparent; border-radius: 12px; padding: 13px 12px; font-size: 10pt; }
.nav-button:hover { background-color: rgba(255,255,255,0.055); color: #F5FBFF; border-color: rgba(255,255,255,0.08); }
.nav-button:checked { background-image: linear-gradient(100deg, rgba(0,242,255,0.17), rgba(112,0,255,0.10)); color: #B8FAFF; border-color: rgba(0,242,255,0.34); box-shadow: inset 3px 0 #00F2FF, 0 5px 18px rgba(0,242,255,0.07); }
.hero { background-image: linear-gradient(112deg, rgba(0,242,255,0.12), rgba(15,23,39,0.70) 48%, rgba(112,0,255,0.12)); background-color: rgba(10,16,28,0.68); border: 1px solid rgba(255,255,255,0.10); border-radius: 22px; box-shadow: 0 20px 46px rgba(0,0,0,0.28); }
.hero-title { color: #F7FBFF; font-size: 20pt; font-weight: 700; }
.hero-copy { color: rgba(225,235,248,0.76); font-size: 10pt; }
.hero-mark { color: rgba(0,242,255,0.92); font-size: 31pt; font-weight: 700; }
.card { background-image: linear-gradient(145deg, rgba(21,30,47,0.78), rgba(8,14,25,0.82)); border: 1px solid rgba(255,255,255,0.08); border-radius: 19px; box-shadow: 0 14px 32px rgba(0,0,0,0.25); }
.card:hover { background-image: linear-gradient(145deg, rgba(25,40,58,0.88), rgba(11,20,33,0.91)); border-color: rgba(0,242,255,0.38); box-shadow: 0 18px 38px rgba(0,0,0,0.35), 0 0 18px rgba(0,242,255,0.10); }
.cover-windows { background-image: linear-gradient(125deg, rgba(0,153,255,0.24), rgba(112,0,255,0.24)); }
.cover-android { background-image: linear-gradient(125deg, rgba(52,211,153,0.19), rgba(0,153,255,0.20)); }
.cover-ios { background-image: linear-gradient(125deg, rgba(170,180,205,0.16), rgba(112,0,255,0.24)); }
.cover-web { background-image: linear-gradient(125deg, rgba(0,242,255,0.22), rgba(55,100,255,0.20)); }
.cover-linux { background-image: linear-gradient(125deg, rgba(255,181,71,0.17), rgba(0,242,255,0.20)); }
.cover-icon { color: #F7FCFF; font-size: 26pt; font-weight: 700; }
.cover-label { color: rgba(240,248,255,0.70); font-size: 8pt; font-weight: 700; letter-spacing: 1.2px; }
.app-name { color: #F6F9FF; font-size: 13pt; font-weight: 700; }
.app-desc { color: rgba(222,232,246,0.70); font-size: 9pt; }
.tag { color: #B5FAFF; background-color: rgba(0,242,255,0.08); border: 1px solid rgba(0,242,255,0.20); border-radius: 9px; padding: 5px 9px; font-size: 8pt; font-weight: 700; }
.verified { color: #86E7C2; font-size: 8pt; }
.primary { background-image: linear-gradient(105deg, #00D9E8, #61EAF2); color: #06121B; border: 1px solid rgba(0,242,255,0.86); border-radius: 11px; padding: 9px 15px; font-weight: 800; box-shadow: 0 5px 18px rgba(0,242,255,0.12); }
.primary:hover { background-image: linear-gradient(105deg, #63F2F8, #A4F7F6); box-shadow: 0 7px 22px rgba(0,242,255,0.24); }
button { background-color: rgba(255,255,255,0.045); color: #E3ECF8; border: 1px solid rgba(255,255,255,0.10); border-radius: 11px; padding: 8px 12px; }
button:hover { background-color: rgba(255,255,255,0.09); color: #FFFFFF; border-color: rgba(0,242,255,0.32); }
button:disabled { color: rgba(215,228,244,0.50); background-color: rgba(255,255,255,0.035); }
dialog, popover, menu { background-color: #0B111D; color: #F3F7FF; border: 1px solid rgba(0,242,255,0.20); border-radius: 14px; }
tooltip { background-color: rgba(5,7,13,0.96); color: #F3F7FF; border: 1px solid rgba(0,242,255,0.24); border-radius: 8px; }
#app-icon { color: #B8FAFF; background-color: rgba(0,242,255,0.08); border: 1px solid rgba(0,242,255,0.18); border-radius: 12px; font-size: 20pt; }
progressbar trough { background-color: rgba(255,255,255,0.09); border-radius: 8px; min-height: 9px; }
progressbar progress { background-image: linear-gradient(90deg, #00D9E8, #7F5BFF); border-radius: 8px; }
separator { background-color: rgba(255,255,255,0.09); }
scrolledwindow { background-color: transparent; }
"""

SECTIONS = [
    ("windows", "▣", "Aplicaciones Windows", ".exe", "Catálogo Winget / Aptoide PC / Classic Games"),
    ("android", "◈", "Aplicaciones APK", ".apk", "Catálogo Aptoide / F-Droid / Aurora"),
    ("ios", "◉", "Aplicaciones iOS", ".ipa", "Catálogo AltStore / SideStore"),
    ("web", "⌘", "Aplicaciones ChromeOS / Web", ".crx / PWA", "Chrome Web Store"),
    ("linux", "⬡", "Aplicaciones Linux", ".deb / Flatpak", "Flathub / Debian Store"),
]

# Package catalog pages are descriptive. Linux Flatpak cards are resolved by app ID
# through OmniLoader; other ecosystems hand the selected package to its runtime.
APPS = {
    "windows": [
        ("7zip", "7-Zip", "Compresor de archivos rápido y de código abierto.", "Winget", "4 MB", "📦", "https://www.7-zip.org/", ".exe"),
        ("vlc-win", "VLC media player", "Reproduce casi cualquier formato de audio y vídeo.", "Winget", "42 MB", "▶", "https://www.videolan.org/vlc/", ".exe"),
        ("classic-games", "Classic Games", "Catálogo de juegos clásicos para Windows; revisa licencia y compatibilidad.", "Aptoide PC", "Variable", "🎮", "https://en.aptoide.com/", ".exe"),
    ],
    "android": [
        ("privacy2048", "2048 (Privacy Friendly)", "Juego de puzles libre de SECUSO, sin anuncios ni permisos.", "F-Droid", "8.9 MB", "2048", "https://f-droid.org/packages/org.secuso.privacyfriendly2048/", ".apk"),
        ("fdroid", "F-Droid", "Cliente de software libre para Android.", "F-Droid", "15 MB", "◈", "https://f-droid.org/", ".apk"),
        ("aurora", "Aurora Store", "Cliente alternativo de código abierto para el catálogo de Play.", "Aptoide / F-Droid", "18 MB", "✦", "https://auroraoss.com/", ".apk"),
        ("vlc-android", "VLC for Android", "Reproductor multimedia de VideoLAN para Android.", "Aptoide", "45 MB", "▶", "https://www.videolan.org/vlc/download-android.html", ".apk"),
    ],
    "ios": [
        ("altstore", "AltStore Classic", "Tienda alternativa para instalar apps propias con Apple ID y límites de firma.", "AltStore", "12 MB", "A", "https://altstore.io/", ".ipa"),
        ("sidestore", "SideStore", "Instalación y refresco de apps firmadas en el dispositivo iOS.", "SideStore", "14 MB", "S", "https://sidestore.io/", ".ipa"),
        ("delta", "Delta Emulator", "Emulador distribuido oficialmente por los canales de AltStore.", "AltStore", "Variable", "🎮", "https://deltaemulator.com/", ".ipa"),
    ],
    "web": [
        ("2048-web", "2048", "Puzle web original, jugable en Chromium como aplicación.", "Web / PWA", "Web", "2048", "https://play2048.co/", ".pwa"),
        ("vscode-web", "Visual Studio Code", "Editor web para trabajar con repositorios y archivos.", "Chrome Web Store / Web", "Web", "⌘", "https://vscode.dev/", ".crx"),
        ("figma", "Figma", "Diseño de interfaces colaborativo en el navegador.", "Chrome Web Store / PWA", "Web", "◉", "https://www.figma.com/", ".crx"),
        ("spotify", "Spotify Web Player", "Música y podcasts desde el navegador.", "Chrome Web Store / PWA", "Web", "♫", "https://open.spotify.com/", ".crx"),
    ],
    "linux": [
        ("gnome-mines", "GNOME Mines", "Buscaminas de GNOME instalado desde Flathub.", "Flathub", "~20 MB + runtime", "✹", "https://flathub.org/apps/org.gnome.Mines", ".flatpak"),
        ("gimp", "GIMP", "Edición y composición de imágenes de código abierto.", "Flathub", "~300 MB", "✎", "https://flathub.org/apps/org.gimp.GIMP", ".flatpak"),
        ("inkscape", "Inkscape", "Ilustración vectorial SVG de calidad profesional.", "Flathub", "~180 MB", "◇", "https://flathub.org/apps/org.inkscape.Inkscape", ".flatpak"),
        ("vlc-linux", "VLC media player", "Reproductor multimedia libre para Linux.", "Flathub", "~100 MB", "▶", "https://flathub.org/apps/org.videolan.VLC", ".flatpak"),
    ],
}

FLATPAK_IDS = {"gnome-mines": "org.gnome.Mines", "gimp": "org.gimp.GIMP", "inkscape": "org.inkscape.Inkscape", "vlc-linux": "org.videolan.VLC"}

STORE_LINKS = [
    ("Aptoide PC", "https://en.aptoide.com/"), ("F-Droid", "https://f-droid.org/"),
    ("Aurora Store", "https://auroraoss.com/"), ("AltStore", "https://altstore.io/"),
    ("SideStore", "https://sidestore.io/"), ("Chrome Web Store", "https://chromewebstore.google.com/"),
    ("Flathub", "https://flathub.org/"), ("Winget", "https://winget.run/"),
]


class OmniStore:
    def __init__(self, args):
        self.args = args
        self.active = "windows"
        self.runtime_recovery_confirmed = False
        self.installed = self._load_installed()
        self.custom_sources = SourceStore()
        self.window = Gtk.Window(title="Nexus OmniStore")
        screen = self.window.get_screen()
        screen_width, screen_height = screen.get_width(), screen.get_height()
        # Keep OmniStore an intentionally floating window with native WM chrome.
        self.window.set_visual(screen.get_rgba_visual() or screen.get_system_visual())
        self.window.set_default_size(max(760, min(960, screen_width - 260)),
                                     max(520, min(620, screen_height - 140)))
        self.window.set_resizable(True)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("destroy", Gtk.main_quit)
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(self.window.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.shell = Gtk.Box(spacing=14)
        self.shell.set_name("app-shell")
        self.shell.get_style_context().add_class("shell")
        self.shell.set_margin_top(14); self.shell.set_margin_bottom(14)
        self.shell.set_margin_start(14); self.shell.set_margin_end(14)
        self.window.add(self.shell)
        self._build_sidebar()
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.content.set_margin_top(22); self.content.set_margin_bottom(18)
        self.content.set_margin_start(20); self.content.set_margin_end(20)
        self.shell.pack_start(self.content, True, True, 0)
        self._render()

    def _load_installed(self):
        try:
            value = json.loads(STATE.read_text())
            return value if isinstance(value, dict) else {}
        except (OSError, ValueError):
            return {}

    def _save_installed(self):
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(self.installed, indent=2))

    def _build_sidebar(self):
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        side.set_size_request(246, -1); side.get_style_context().add_class("sidebar")
        side.set_margin_top(8); side.set_margin_start(5); side.set_margin_end(5); side.set_margin_bottom(8)
        brand = Gtk.Label(); brand.set_markup('<span foreground="#F5FBFF" size="x-large" weight="heavy">NEXUS</span> <span foreground="#00F0FF" size="x-large" weight="heavy">OMNI</span>')
        brand.set_xalign(0); side.pack_start(brand, False, False, 7)
        caption = Gtk.Label(label="UNIFIED APP EXPERIENCE"); caption.get_style_context().add_class("eyebrow"); caption.set_xalign(0)
        side.pack_start(caption, False, False, 0)
        sep = Gtk.Separator(); side.pack_start(sep, False, False, 10)
        self.nav = Gtk.RadioButton.new_with_label_from_widget(None, "")
        self.nav_buttons = {}
        for idx, (key, icon, label, ext, source) in enumerate(SECTIONS):
            button = Gtk.RadioButton.new_with_label_from_widget(self.nav if idx else None, f"{icon}    {label}")
            if idx == 0: self.nav = button
            button.set_mode(False); button.get_style_context().add_class("nav-button")
            button.connect("toggled", self._navigate, key)
            side.pack_start(button, False, False, 0); self.nav_buttons[key] = button
        side.pack_start(Gtk.Box(), True, True, 0)
        store_label = Gtk.Label(label="TIENDAS OFICIALES"); store_label.get_style_context().add_class("eyebrow"); store_label.set_xalign(0)
        side.pack_start(store_label, False, False, 4)
        store_scroll = Gtk.ScrolledWindow()
        store_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        store_scroll.set_min_content_height(160)
        store_scroll.set_max_content_height(280)
        store_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        store_scroll.add(store_list)
        for name, url in STORE_LINKS:
            button = Gtk.Button(label=f"↗   {name}"); button.set_relief(Gtk.ReliefStyle.NONE); button.set_halign(Gtk.Align.FILL)
            button.connect("clicked", lambda _b, u=url: self._open_url(u))
            store_list.pack_start(button, False, False, 0)
        custom_title = Gtk.Label(label="MIS TIENDAS"); custom_title.get_style_context().add_class("eyebrow"); custom_title.set_xalign(0)
        custom_title.set_margin_top(12); custom_title.set_margin_start(9)
        store_list.pack_start(custom_title, False, False, 5)
        self.custom_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        store_list.pack_start(self.custom_list, False, False, 0)
        self.custom_scroll = store_scroll
        side.pack_start(store_scroll, True, True, 0)
        add_store = Gtk.Button(label="＋  Añadir tienda")
        add_store.get_style_context().add_class("primary")
        add_store.connect("clicked", self._add_store_dialog)
        side.pack_start(add_store, False, False, 0)
        self._render_custom_sources()
        self.shell.pack_start(side, False, False, 0)

    def _render_custom_sources(self):
        for child in self.custom_list.get_children(): self.custom_list.remove(child)
        sources = self.custom_sources.list()
        if not sources:
            empty = Gtk.Label(label="Añade una tienda HTTPS")
            empty.get_style_context().add_class("muted"); empty.set_xalign(0)
            empty.set_margin_start(12); empty.set_margin_top(3); empty.set_margin_bottom(6)
            self.custom_list.pack_start(empty, False, False, 0)
        for source in sources:
            row = Gtk.Box(spacing=3)
            open_button = Gtk.Button(label=f"↗   {source['name']}")
            open_button.set_relief(Gtk.ReliefStyle.NONE); open_button.set_halign(Gtk.Align.FILL)
            open_button.set_tooltip_text(source["url"])
            open_button.connect("clicked", self._open_custom_source, source)
            row.pack_start(open_button, True, True, 0)
            remove = Gtk.Button(label="×"); remove.set_relief(Gtk.ReliefStyle.NONE)
            remove.set_tooltip_text("Quitar esta tienda de OmniStore")
            remove.connect("clicked", self._remove_custom_source, source["id"])
            row.pack_end(remove, False, False, 0)
            self.custom_list.pack_start(row, False, False, 0)
        self.custom_list.show_all()

    def _open_custom_source(self, _button, source):
        self._open_url(source["url"])
        self.status.set_text(f"Abriendo {source['name']}. Descarga un paquete compatible y selecciónalo en su sección para instalarlo con OmniLoader.")

    def _remove_custom_source(self, _button, source_id):
        self.custom_sources.remove(source_id)
        self._render_custom_sources()

    def _add_store_dialog(self, _button):
        if len(self.custom_sources.list()) >= 100:
            self.status.set_text("Llegaste al máximo de 100 tiendas personalizadas.")
            return
        dialog = Gtk.Dialog(title="Añadir tienda de aplicaciones", parent=self.window, flags=Gtk.DialogFlags.MODAL)
        dialog.add_buttons("Cancelar", Gtk.ResponseType.CANCEL, "Añadir tienda", Gtk.ResponseType.OK)
        dialog.set_default_size(520, 260)
        body = dialog.get_content_area()
        body.set_spacing(10); body.set_margin_top(16); body.set_margin_bottom(14); body.set_margin_start(18); body.set_margin_end(18)
        body.pack_start(self._label("Registra el enlace HTTPS de una tienda o catálogo legal.", "app-name"), False, False, 0)
        body.pack_start(self._label("OmniStore guarda el enlace HTTPS y lo abre en el navegador; no verifica automáticamente la legalidad del catálogo. Para instalar, usa el flujo compatible de la sección correspondiente.", "app-desc"), False, False, 0)
        name = Gtk.Entry(); name.set_placeholder_text("Nombre de la tienda"); body.pack_start(name, False, False, 0)
        url = Gtk.Entry(); url.set_placeholder_text("https://tienda.example"); body.pack_start(url, False, False, 0)
        error = Gtk.Label(); error.set_xalign(0); error.set_line_wrap(True)
        error.get_style_context().add_class("status"); body.pack_start(error, False, False, 0)
        consent = Gtk.CheckButton(label="Confirmo que esta tienda es legítima y que tengo derecho a usarla.")
        body.pack_start(consent, False, False, 0)
        accept = dialog.get_widget_for_response(Gtk.ResponseType.OK)
        accept.set_sensitive(False)
        consent.connect("toggled", lambda item: accept.set_sensitive(item.get_active()))
        dialog.show_all()
        while True:
            if dialog.run() != Gtk.ResponseType.OK:
                break
            try:
                self.custom_sources.add(name.get_text(), url.get_text())
                self._render_custom_sources()
                self.status.set_text("Tienda añadida. OmniStore conserva el enlace en este perfil de usuario.")
                break
            except ValueError as exc:
                error.set_text(str(exc))
                dialog.show_all()
            except OSError as exc:
                error.set_text(f"No se pudo guardar la tienda: {exc}")
                dialog.show_all()
        dialog.destroy()

    def _navigate(self, button, key):
        if button.get_active():
            self.active = key
            self._render()

    def _clear(self):
        for child in self.content.get_children(): self.content.remove(child)

    def _label(self, text, style=None, x=0):
        label = Gtk.Label(label=text); label.set_xalign(x)
        if style: label.get_style_context().add_class(style)
        return label

    def _render(self):
        self.window.set_title("Nexus OmniStore")
        self._clear()
        section = next(item for item in SECTIONS if item[0] == self.active)
        _, icon, heading, ext, source = section
        eyebrow = self._label("NEXUS OMNISTORE   /   CATÁLOGO UNIFICADO", "eyebrow")
        self.content.pack_start(eyebrow, False, False, 0)
        self.content.pack_start(self._label(heading, "headline"), False, False, 0)
        self.content.pack_start(self._label(f"{source}     •     {ext}     •     Instalación mediada por Nexus OmniLoader", "muted"), False, False, 0)
        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8); hero.get_style_context().add_class("hero")
        hero.set_margin_top(3); hero.set_margin_bottom(3); hero.set_margin_start(1); hero.set_margin_end(1)
        hero.set_border_width(20)
        hero_row = Gtk.Box(spacing=18)
        hero_copy_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        hero_copy_box.pack_start(self._label("Un solo lugar. Todo tu ecosistema.", "hero-title"), False, False, 0)
        hero_copy = ("Elige una aplicación de Flathub: Nexus OmniLoader la instala y la ejecuta en este perfil de usuario."
                     if self.active == "linux" else
                     "Explora catálogos oficiales. Descarga desde el editor y elige el paquete para instalarlo con la ruta compatible de Nexus.")
        hero_copy_box.pack_start(self._label(hero_copy, "hero-copy"), False, False, 0)
        hero_row.pack_start(hero_copy_box, True, True, 0)
        hero_row.pack_end(self._label(f"{icon}\nNEXUS RUNTIME", "hero-mark"), False, False, 0)
        hero.pack_start(hero_row, False, False, 0)
        self.content.pack_start(hero, False, False, 0)
        if self.active == "linux":
            add_flatpak = Gtk.Button(label="＋  Instalar aplicación Flathub por ID")
            add_flatpak.get_style_context().add_class("primary")
            add_flatpak.set_halign(Gtk.Align.START)
            add_flatpak.connect("clicked", self._install_flatpak_dialog)
            self.content.pack_start(add_flatpak, False, False, 0)
        scroll = Gtk.ScrolledWindow(); scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_overlay_scrolling(True)
        grid = Gtk.FlowBox(); grid.set_selection_mode(Gtk.SelectionMode.NONE); grid.set_max_children_per_line(3); grid.set_min_children_per_line(1); grid.set_column_spacing(18); grid.set_row_spacing(18)
        scroll.add(grid); self.content.pack_start(scroll, True, True, 0)
        rows = list(APPS[self.active])
        if self.active == "linux":
            catalog_ids = {row[0] for row in rows}
            for app_id, installed in self.installed.items():
                if app_id not in catalog_ids and isinstance(installed, str) and installed.startswith("flatpak:"):
                    flatpak_id = installed.partition(":")[2]
                    rows.append((app_id, flatpak_id, "Aplicación Flatpak instalada desde Flathub.", "Flathub", "Variable", "⬡", f"https://flathub.org/apps/{flatpak_id}", ".flatpak"))
        for app in rows: grid.add(self._card(app))
        self.status = Gtk.Label(label="Catálogo curado · verifica editor, permisos y compatibilidad antes de instalar.")
        self.status.get_style_context().add_class("muted"); self.status.set_xalign(0)
        self.content.pack_start(Gtk.Separator(), False, False, 0)
        self.content.pack_start(self.status, False, False, 0)
        self.window.show_all()

    def _card(self, app):
        app_id, name, desc, origin, size, glyph, url, ext = app
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10); box.get_style_context().add_class("card")
        box.set_size_request(250, 286); box.set_border_width(15)
        cover = Gtk.Box(spacing=13); cover.get_style_context().add_class("cover")
        cover.get_style_context().add_class(f"cover-{self.active}")
        cover.set_size_request(-1, 82); cover.set_border_width(13)
        real_icon = os.environ.get("NEXUS_ANDROID_REAL_ICON") if app_id == "privacy2048" else None
        if real_icon and Path(real_icon).is_file():
            logo = Gtk.Image.new_from_file(real_icon); logo.set_size_request(54, 54)
        else:
            logo = Gtk.Label(label=glyph); logo.set_size_request(54, 54)
            logo.get_style_context().add_class("cover-icon")
        logo.set_name("app-icon")
        cover.pack_start(logo, False, False, 0)
        cover_text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        cover_text.pack_start(self._label(self.active.upper(), "cover-label"), False, False, 0)
        cover_text.pack_start(self._label(f"NEXUS · {ext.upper()}", "cover-label"), False, False, 0)
        cover.pack_start(cover_text, True, True, 0)
        box.pack_start(cover, False, False, 0)
        titlebox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        titlebox.set_margin_top(2)
        titlebox.pack_start(self._label(name, "app-name"), False, False, 0)
        verified = self._label(f"✓  Catálogo de {origin}", "verified")
        titlebox.pack_start(verified, False, False, 0)
        box.pack_start(titlebox, False, False, 0)
        box.pack_start(self._label(desc, "app-desc"), True, True, 0)
        meta = Gtk.Box(spacing=6); meta.pack_start(self._label(origin, "tag"), False, False, 0); meta.pack_start(self._label(size, "muted"), False, False, 0)
        box.pack_start(meta, False, False, 0)
        button_row = Gtk.Box(spacing=8)
        installed_path = self.installed.get(app_id)
        install = Gtk.Button(label="Instalado ✓" if installed_path else "Instalar")
        install.get_style_context().add_class("primary")
        install.set_sensitive(not bool(installed_path))
        install.connect("clicked", self._install_clicked, app)
        button_row.pack_start(install, True, True, 0)
        open_button = Gtk.Button(label="Abrir" if installed_path else "Ver tienda")
        open_button.connect("clicked", self._open_clicked, app, installed_path)
        button_row.pack_start(open_button, False, False, 0)
        box.pack_end(button_row, False, False, 0)
        return box

    def _open_url(self, url):
        try: subprocess.Popen(["xdg-open", url], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
        except OSError as exc: self.status.set_text(f"No se pudo abrir el catálogo: {exc}")

    def _open_clicked(self, _button, app, installed_path):
        if installed_path:
            if installed_path.startswith("flatpak:"):
                self._launch_flatpak(installed_path.partition(":")[2])
            elif installed_path.startswith("web:"):
                self._open_webapp(installed_path.partition(":")[2])
            else:
                self._run_loader(installed_path, app[0], auto=False, action="open")
        else:
            self._open_url(app[6])

    def _install_clicked(self, _button, app):
        app_id, name, desc, origin, _size, _glyph, url, extension = app
        if self.active == "linux" and extension == ".flatpak":
            self._install_flatpak(FLATPAK_IDS.get(app_id, app_id), app_id, self.args.auto_launch)
            return
        if self.active == "windows" and app_id == "7zip":
            self._run_loader("7zip:auto", app_id, self.args.auto_launch)
            return
        if self.active == "web" and extension == ".pwa":
            self.status.set_text(f"Cargando {name} en Chromium mediante Nexus OmniLoader…")
            self.window.set_title(f"Nexus OmniStore · Cargando {name}…")
            progress = Gtk.ProgressBar(); progress.set_show_text(True)
            progress.set_text("Preparando aplicación web…"); progress.set_pulse_step(0.08)
            self.content.pack_start(progress, False, False, 0); self.window.show_all()
            started_at = time.monotonic()
            try:
                process = subprocess.Popen(self._runtime_command("install", "web", url), stdin=subprocess.DEVNULL,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True,
                                           start_new_session=True, env=self._runtime_environment())
            except OSError as exc:
                progress.destroy()
                self.status.set_text(f"No se pudo iniciar Chromium: {exc}")
                self.window.set_title("Nexus OmniStore · No se pudo abrir la PWA")
                return

            def finish_web_launch():
                progress.destroy()
                if process.returncode == 0:
                    self.installed[app_id] = f"web:{url}"; self._save_installed(); self._render()
                    self.status.set_text(f"PWA abierta ✓  {name} · Chromium ejecuta la aplicación web real")
                    self.window.set_title(f"Nexus OmniStore · Abierta {name} ✓")
                else:
                    self.status.set_text(f"No se pudo abrir {name} mediante Nexus OmniLoader (código {process.returncode}).")
                    self.window.set_title("Nexus OmniStore · No se pudo abrir la PWA")
                return False

            def poll_web_launch():
                if process.poll() is None:
                    progress.pulse()
                    return True
                elapsed = time.monotonic() - started_at
                if elapsed < MIN_INSTALL_STATE_SECONDS:
                    progress.set_fraction(1.0); progress.set_text("Verificando apertura… 100%")
                    self.status.set_text(f"Cargando {name}… verificando la apertura en Chromium.")
                    GLib.timeout_add(max(1, int((MIN_INSTALL_STATE_SECONDS - elapsed) * 1000)), finish_web_launch)
                else:
                    finish_web_launch()
                return False

            GLib.timeout_add(120, poll_web_launch)
            return
        self.status.set_text(f"Abriendo {origin}. Descarga {name} y luego selecciona el archivo {extension} aquí.")
        self._open_url(url)
        chooser = Gtk.FileChooserDialog(title=f"Seleccionar paquete para {name}", parent=self.window, action=Gtk.FileChooserAction.OPEN)
        chooser.add_buttons("Cancelar", Gtk.ResponseType.CANCEL, "Instalar con Nexus", Gtk.ResponseType.ACCEPT)
        chooser.set_select_multiple(False)
        chooser.set_current_folder(str(HOME / "Downloads") if (HOME / "Downloads").is_dir() else str(HOME))
        chooser.set_filter(self._filter(extension))
        response = chooser.run(); filename = chooser.get_filename(); chooser.destroy()
        if response != Gtk.ResponseType.ACCEPT or not filename: return
        self._run_loader(filename, app_id, self.args.auto_launch)

    @staticmethod
    def _valid_flatpak_id(app_id):
        return len(app_id) <= 255 and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,62}(?:\.[A-Za-z0-9][A-Za-z0-9_-]{0,62})+", app_id))

    def _install_flatpak_dialog(self, _button):
        dialog = Gtk.Dialog(title="Instalar aplicación Flathub", parent=self.window, flags=Gtk.DialogFlags.MODAL)
        dialog.add_buttons("Cancelar", Gtk.ResponseType.CANCEL, "Continuar", Gtk.ResponseType.OK)
        body = dialog.get_content_area(); body.set_spacing(10)
        body.set_margin_top(16); body.set_margin_bottom(14); body.set_margin_start(18); body.set_margin_end(18)
        body.pack_start(self._label("Introduce el ID exacto de la aplicación, por ejemplo org.gimp.GIMP.", "app-desc"), False, False, 0)
        entry = Gtk.Entry(); entry.set_max_length(255); entry.set_placeholder_text("org.ejemplo.Aplicacion"); body.pack_start(entry, False, False, 0)
        error = Gtk.Label(); error.set_xalign(0); body.pack_start(error, False, False, 0)
        dialog.show_all()
        while dialog.run() == Gtk.ResponseType.OK:
            app_id = entry.get_text().strip()
            if not self._valid_flatpak_id(app_id):
                error.set_text("ID no válido. Usa el ID inverso de Flathub, sin espacios ni opciones de terminal.")
                dialog.show_all(); continue
            dialog.destroy()
            custom_id = f"flathub:{app_id}"
            self._install_flatpak(app_id, custom_id, self.args.auto_launch)
            return
        dialog.destroy()

    def _install_flatpak(self, flatpak_id, store_id, auto=False):
        if not self._valid_flatpak_id(flatpak_id):
            self.status.set_text("ID Flatpak no válido."); return
        self.status.set_text(f"Conectando con Nexus OmniLoader para instalar {flatpak_id} desde Flathub…")
        self.window.set_title(f"Nexus OmniStore · Instalando {flatpak_id}…")
        progress = Gtk.ProgressBar(); progress.set_show_text(True); progress.set_text("Instalando con OmniLoader…")
        progress.set_pulse_step(0.08)
        self.content.pack_start(progress, False, False, 0); self.window.show_all()
        try:
            log = tempfile.TemporaryFile(mode="w+t")
            started_at = time.monotonic()
            process = subprocess.Popen(self._runtime_command("install", "linux", f"flatpak:{flatpak_id}"),
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                       text=True, close_fds=True, env=self._runtime_environment())
        except OSError as exc:
            progress.destroy()
            self.window.set_title("Nexus OmniStore"); self.status.set_text(f"No se pudo iniciar OmniLoader: {exc}"); return

        def finish_install(code, output):
            progress.destroy()
            if code != 0 and self.runtime_recovery_confirmed:
                return False
            if code == 0:
                self.installed[store_id] = f"flatpak:{flatpak_id}"; self._save_installed()
                self._render()
                self.status.set_text(f"Instalado ✓  {flatpak_id} por Nexus OmniLoader · pulsa Abrir para ejecutarlo")
                self.window.set_title(f"Nexus OmniStore · Instalado {flatpak_id} ✓")
                if auto: GLib.timeout_add(300, lambda: self._launch_flatpak(flatpak_id) or False)
            else:
                detail = output[-240:] if output else f"OmniLoader terminó con código {code}."
                self.status.set_text(f"Instalación no completada: {detail}")
                self.window.set_title("Nexus OmniStore · Instalación no completada")
            return False

        def poll():
            log.flush(); log.seek(0); output = log.read()
            percentages = [int(value) for value in re.findall(r"(?<!\d)(\d{1,3})%", output) if int(value) <= 100]
            if percentages:
                percent = percentages[-1]
                progress.set_fraction(percent / 100.0)
                progress.set_text(f"Descargando e instalando… {percent}%")
            elif process.poll() is None:
                progress.pulse()
            if process.poll() is None:
                return True
            log.seek(0); output = log.read().strip(); log.close()
            elapsed = time.monotonic() - started_at
            if elapsed < MIN_INSTALL_STATE_SECONDS:
                progress.set_fraction(1.0)
                progress.set_text("Verificando paquete… 100%")
                self.status.set_text("Instalando… verificando el resultado con Nexus OmniLoader.")
                GLib.timeout_add(max(1, int((MIN_INSTALL_STATE_SECONDS - elapsed) * 1000)),
                                 lambda: finish_install(process.returncode, output))
            else:
                finish_install(process.returncode, output)
            return False
        GLib.timeout_add(140, poll)

    def _launch_flatpak(self, flatpak_id):
        try:
            subprocess.Popen(self._runtime_command("open", "linux", f"flatpak:{flatpak_id}"), stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             close_fds=True, start_new_session=True, env=self._runtime_environment())
            self.status.set_text(f"Aplicación iniciada mediante Nexus OmniLoader: {flatpak_id}")
        except OSError as exc:
            self.status.set_text(f"No se pudo iniciar OmniLoader: {exc}")

    def _open_webapp(self, url):
        try:
            subprocess.Popen(self._runtime_command("open", "web", url), stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True,
                             start_new_session=True, env=self._runtime_environment())
            self.status.set_text(f"Aplicación web iniciada en Chromium: {url}")
        except OSError as exc:
            self.status.set_text(f"No se pudo iniciar la PWA: {exc}")

    @staticmethod
    def _filter(extension):
        file_filter = Gtk.FileFilter(); file_filter.set_name(f"Paquetes {extension}")
        patterns = {".exe": ("*.exe", "*.msi"), ".apk": ("*.apk",), ".ipa": ("*.ipa",), ".crx": ("*.crx",), ".deb": ("*.deb",)}
        for pattern in patterns.get(extension, ("*",)): file_filter.add_pattern(pattern)
        return file_filter

    def _runtime_script(self):
        configured = os.environ.get("NEXUS_RUNTIME_SMOKE")
        candidates = [Path(configured)] if configured else []
        candidates.extend((Path(__file__).resolve().parents[3] / "runtime-smoke.sh",
                           Path("/usr/lib/nexus/nexus-runtime-smoke.sh")))
        return next((path for path in candidates if path.is_file()), None)

    def _runtime_environment(self):
        environment = os.environ.copy()
        if "NEXUS_OMNILOADER" not in environment:
            staged = Path(__file__).resolve().parents[3] / "staging/usr/bin/nexus-omniloader"
            environment["NEXUS_OMNILOADER"] = str(staged if staged.is_file() else "/usr/bin/nexus-omniloader")
        return environment

    def _runtime_command(self, action, ecosystem, target):
        script = self._runtime_script()
        if script:
            return ["bash", str(script), f"--store-{action}", ecosystem, str(target)]
        loader = os.environ.get("NEXUS_OMNILOADER", "/usr/bin/nexus-omniloader")
        if str(target).startswith("flatpak:"):
            flag = "--install-flatpak" if action == "install" else "--run-flatpak"
            return [loader, flag, str(target).partition(":")[2]]
        return [loader, str(target)]

    def _runtime_recovery_verified(self, _signum=None, _frame=None):
        """Record recovery only after the evidence driver has mapped the real app."""
        GLib.idle_add(self._apply_runtime_recovery_verified)

    def _apply_runtime_recovery_verified(self):
        self.runtime_recovery_confirmed = True
        app_id = self.args.install_app or ""
        if app_id == "7zip":
            installed_value = "7zip:auto"
        elif app_id == "privacy2048" and self.args.package_path:
            installed_value = str(Path(self.args.package_path).expanduser().resolve())
        elif app_id == "2048-web":
            installed_value = "web:https://play2048.co/"
        elif app_id in FLATPAK_IDS:
            installed_value = f"flatpak:{FLATPAK_IDS[app_id]}"
        else:
            installed_value = self.args.package_path or ""
        if app_id and installed_value:
            self.installed[app_id] = installed_value
            self._save_installed()
            self._render()
            self.status.set_text(f"Instalado ✓  {app_id}; ventana real verificada por el runtime integrado.")
            self.window.set_title(f"Nexus OmniStore · Instalado {app_id} ✓")
        return GLib.SOURCE_REMOVE

    def _run_loader(self, filename, app_id, auto=False, action="install"):
        is_automatic_package = filename == "7zip:auto"
        path = str(Path(filename).expanduser().resolve())
        if not is_automatic_package and not Path(path).is_file():
            self.status.set_text("No se encontró el paquete seleccionado."); return
        if is_automatic_package:
            path = filename
        self.status.set_text("Instalando… Nexus OmniLoader está procesando el paquete seleccionado.")
        self.window.set_title(f"Nexus OmniStore · Instalando {app_id}…")
        progress = Gtk.ProgressBar(); progress.set_show_text(True); progress.set_text("Instalando…")
        self.content.pack_start(progress, False, False, 0); self.window.show_all()
        try:
            log = tempfile.TemporaryFile(mode="w+t")
            started_at = time.monotonic()
            process = subprocess.Popen(self._runtime_command(action, self.active, path), stdin=subprocess.DEVNULL,
                                       stdout=log, stderr=subprocess.STDOUT, text=True, close_fds=True,
                                       env=self._runtime_environment())
        except OSError as exc:
            progress.destroy(); self.window.set_title("Nexus OmniStore"); self.status.set_text(f"No se pudo iniciar OmniLoader: {exc}"); return
        # OmniLoader does not expose fractional progress; show an honest live pulse
        # while the child runs, then record success only on its zero exit status.
        def finish_install(code, output):
            progress.destroy()
            if code != 0 and self.runtime_recovery_confirmed:
                return False
            if code == 0:
                self.installed[app_id] = path; self._save_installed()
                self._render()
                self.status.set_text(f"Instalado ✓  {Path(path).name}")
                self.window.set_title(f"Nexus OmniStore · Instalado {app_id} ✓")
                if auto: GLib.timeout_add(300, lambda: self._run_loader(path, app_id, auto=False, action="open") or False)
            else:
                detail = output[-180:] if output else f"OmniLoader terminó con código {code}."
                self.status.set_text(f"Instalación no completada: {detail}")
                self.window.set_title("Nexus OmniStore · Instalación no completada")
            return False

        def poll():
            code = process.poll()
            if code is None:
                progress.pulse(); return True
            log.seek(0)
            output = log.read().strip()
            log.close()
            elapsed = time.monotonic() - started_at
            if action == "install" and elapsed < MIN_INSTALL_STATE_SECONDS:
                progress.set_fraction(1.0)
                progress.set_text("Verificando paquete… 100%")
                self.status.set_text("Instalando… verificando el resultado con Nexus OmniLoader.")
                GLib.timeout_add(max(1, int((MIN_INSTALL_STATE_SECONDS - elapsed) * 1000)),
                                 lambda: finish_install(code, output))
            else:
                finish_install(code, output)
            return False
        GLib.timeout_add(140, poll)

    def run(self):
        if self.args.install_app:
            signal.signal(signal.SIGUSR1, self._runtime_recovery_verified)
        key = self.args.select_tab
        if key in self.nav_buttons:
            self.nav_buttons[key].set_active(True)
        self.window.show_all()
        if self.args.install_app:
            found = next((app for rows in APPS.values() for app in rows if app[0] == self.args.install_app), None)
            if not found:
                raise SystemExit(f"Aplicación desconocida: {self.args.install_app}")
            self.active = next(key for key, rows in APPS.items() if found in rows)
            self.nav_buttons[self.active].set_active(True)
            self._render()
            if self.args.package_path:
                self._run_loader(self.args.package_path, found[0], self.args.auto_launch)
            elif self.active == "linux":
                self._install_flatpak(FLATPAK_IDS.get(found[0], found[0]), found[0], self.args.auto_launch)
            else:
                GLib.timeout_add(250, lambda: self._install_clicked(None, found) or False)
        elif self.args.flatpak_id:
            self.active = "linux"; self.nav_buttons["linux"].set_active(True); self._render()
            self._install_flatpak(self.args.flatpak_id, f"flathub:{self.args.flatpak_id}", self.args.auto_launch)
        Gtk.main()


def main():
    parser = argparse.ArgumentParser(description="Nexus OmniStore")
    parser.add_argument("--select-tab", choices=[section[0] for section in SECTIONS], default="windows")
    parser.add_argument("--install-app", help="Instala una aplicación del catálogo por identificador")
    parser.add_argument("--package-path", help="Ruta local del paquete para automatización (opcional)")
    parser.add_argument("--flatpak-id", help="Instala un ID de aplicación Flathub mediante Nexus OmniLoader")
    parser.add_argument("--auto-launch", action="store_true", help="Abre el paquete al terminar una instalación correcta")
    args = parser.parse_args()
    OmniStore(args).run()


if __name__ == "__main__":
    main()
