#!/usr/bin/env python3
"""Nexus OmniStore: curated storefront directory and safe package handoff UI."""
import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk
from omni_store_sources import SourceStore


HOME = Path.home()
STATE = HOME / ".local/share/nexus/omnistore-installed.json"
CSS = """
window { background: #0B0F19; color: #ECF7FF; font-family: Inter, 'Noto Sans', sans-serif; }
.sidebar { background: #0D1320; border-right: 1px solid #1B293B; }
.brand { color: #F5FBFF; font-size: 19pt; font-weight: 800; }
.brand-accent { color: #00F0FF; }
.eyebrow { color: #00F0FF; font-size: 9pt; font-weight: 700; letter-spacing: 1.4px; }
.headline { color: #F5FBFF; font-size: 25pt; font-weight: 800; }
.muted { color: #93A7BE; }
.nav-button { background: transparent; color: #9FB1C6; border: 1px solid transparent; border-radius: 10px; padding: 12px; font-size: 10pt; }
.nav-button:hover { background: #121E2D; color: #ECF7FF; }
.nav-button:checked { background: #102432; color: #72F5FF; border-color: #00BFD0; }
.hero { background: linear-gradient(120deg, #10253A, #1C1630); border: 1px solid #225165; border-radius: 18px; }
.hero-title { color: #F7FCFF; font-size: 18pt; font-weight: 800; }
.hero-copy { color: #AEC1D5; font-size: 10pt; }
.card { background: #111927; border: 1px solid #253449; border-radius: 15px; }
.card:hover { border-color: #00BFD0; }
.app-name { color: #F1F8FF; font-size: 13pt; font-weight: 700; }
.app-desc { color: #A8B9CC; font-size: 9pt; }
.tag { color: #91F8FF; background: #102B38; border: 1px solid #176174; border-radius: 9px; padding: 4px 8px; font-size: 8pt; font-weight: 700; }
.verified { color: #6EF0B1; }
.primary { background: #00D9E8; color: #06121B; border: 1px solid #00F0FF; border-radius: 9px; padding: 8px 14px; font-weight: 800; }
.primary:hover { background: #75F5FF; }
button { background: #182438; color: #DCEBFA; border: 1px solid #30445D; border-radius: 9px; padding: 7px 12px; }
button:hover { background: #20334B; border-color: #00BFD0; }
#app-icon { color: #83F7FF; background: #15283B; border-radius: 12px; font-size: 20pt; }
progressbar trough { background: #1B293B; border-radius: 8px; min-height: 9px; }
progressbar progress { background: #00E3F1; border-radius: 8px; }
separator { background: #1C2A3B; }
"""

SECTIONS = [
    ("windows", "▣", "Aplicaciones Windows", ".exe", "Catálogo Winget / Aptoide PC / Classic Games"),
    ("android", "◈", "Aplicaciones APK", ".apk", "Catálogo Aptoide / F-Droid / Aurora"),
    ("ios", "◉", "Aplicaciones iOS", ".ipa", "Catálogo AltStore / SideStore"),
    ("web", "⌘", "Aplicaciones ChromeOS / Web", ".crx / PWA", "Chrome Web Store"),
    ("linux", "⬡", "Aplicaciones Linux", ".deb / Flatpak", "Flathub / Debian Store"),
]

# Catalog entries link to their publishers/store listings. OmniStore never silently
# installs a remote binary: the user chooses the downloaded package before OmniLoader.
APPS = {
    "windows": [
        ("7zip", "7-Zip", "Compresor de archivos rápido y de código abierto.", "Winget", "4 MB", "📦", "https://www.7-zip.org/", ".exe"),
        ("vlc-win", "VLC media player", "Reproduce casi cualquier formato de audio y vídeo.", "Winget", "42 MB", "▶", "https://www.videolan.org/vlc/", ".exe"),
        ("classic-games", "Classic Games", "Catálogo de juegos clásicos para Windows; revisa licencia y compatibilidad.", "Aptoide PC", "Variable", "🎮", "https://en.aptoide.com/", ".exe"),
    ],
    "android": [
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
        ("vscode-web", "Visual Studio Code", "Editor web para trabajar con repositorios y archivos.", "Chrome Web Store / Web", "Web", "⌘", "https://vscode.dev/", ".crx"),
        ("figma", "Figma", "Diseño de interfaces colaborativo en el navegador.", "Chrome Web Store / PWA", "Web", "◉", "https://www.figma.com/", ".crx"),
        ("spotify", "Spotify Web Player", "Música y podcasts desde el navegador.", "Chrome Web Store / PWA", "Web", "♫", "https://open.spotify.com/", ".crx"),
    ],
    "linux": [
        ("gimp", "GIMP", "Edición y composición de imágenes de código abierto.", "Flathub", "~300 MB", "✎", "https://flathub.org/apps/org.gimp.GIMP", ".deb"),
        ("inkscape", "Inkscape", "Ilustración vectorial SVG de calidad profesional.", "Flathub", "~180 MB", "◇", "https://flathub.org/apps/org.inkscape.Inkscape", ".deb"),
        ("vlc-linux", "VLC media player", "Reproductor multimedia libre para Linux.", "Debian Store / Flathub", "~100 MB", "▶", "https://flathub.org/apps/org.videolan.VLC", ".deb"),
    ],
}

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
        self.installed = self._load_installed()
        self.custom_sources = SourceStore()
        self.window = Gtk.Window(title="Nexus OmniStore")
        self.window.set_default_size(1240, 820)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("destroy", Gtk.main_quit)
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(self.window.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.shell = Gtk.Box(spacing=0)
        self.window.add(self.shell)
        self._build_sidebar()
        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.content.set_margin_top(30); self.content.set_margin_bottom(24)
        self.content.set_margin_start(30); self.content.set_margin_end(30)
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
        side.set_size_request(270, -1); side.get_style_context().add_class("sidebar")
        side.set_margin_top(28); side.set_margin_start(18); side.set_margin_end(16); side.set_margin_bottom(20)
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
        body.pack_start(self._label("OmniStore guarda el enlace HTTPS y lo abre en el navegador; no verifica automáticamente la legalidad del catálogo. Para instalar, descarga un paquete y selecciónalo en la sección compatible. No ejecutamos descargas automáticamente.", "app-desc"), False, False, 0)
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
        hero.pack_start(self._label("Un solo lugar. Todo tu ecosistema.", "hero-title"), False, False, 0)
        hero.pack_start(self._label("Explora catálogos oficiales. Descarga desde el editor y elige el paquete para instalarlo con la ruta compatible de Nexus.", "hero-copy"), False, False, 0)
        self.content.pack_start(hero, False, False, 0)
        scroll = Gtk.ScrolledWindow(); scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        grid = Gtk.FlowBox(); grid.set_selection_mode(Gtk.SelectionMode.NONE); grid.set_max_children_per_line(3); grid.set_min_children_per_line(1); grid.set_column_spacing(14); grid.set_row_spacing(14)
        scroll.add(grid); self.content.pack_start(scroll, True, True, 0)
        for app in APPS[self.active]: grid.add(self._card(app))
        self.status = Gtk.Label(label="Catálogo curado · verifica editor, permisos y compatibilidad antes de instalar.")
        self.status.get_style_context().add_class("muted"); self.status.set_xalign(0)
        self.content.pack_start(Gtk.Separator(), False, False, 0)
        self.content.pack_start(self.status, False, False, 0)
        self.window.show_all()

    def _card(self, app):
        app_id, name, desc, origin, size, glyph, url, ext = app
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10); box.get_style_context().add_class("card")
        box.set_size_request(260, 218); box.set_border_width(17)
        top = Gtk.Box(spacing=10)
        logo = Gtk.Label(label=glyph); logo.set_size_request(40, 40); logo.set_name("app-icon")
        top.pack_start(logo, False, False, 0)
        titlebox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        titlebox.pack_start(self._label(name, "app-name"), False, False, 0)
        verified = self._label("✓  Fuente verificada", "verified"); titlebox.pack_start(verified, False, False, 0)
        top.pack_start(titlebox, True, True, 0); box.pack_start(top, False, False, 0)
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
            self._run_loader(installed_path, app[0], auto=False)
        else:
            self._open_url(app[6])

    def _install_clicked(self, _button, app):
        app_id, name, desc, origin, _size, _glyph, url, extension = app
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
    def _filter(extension):
        file_filter = Gtk.FileFilter(); file_filter.set_name(f"Paquetes {extension}")
        patterns = {".exe": ("*.exe", "*.msi"), ".apk": ("*.apk",), ".ipa": ("*.ipa",), ".crx": ("*.crx",), ".deb": ("*.deb",)}
        for pattern in patterns.get(extension, ("*",)): file_filter.add_pattern(pattern)
        return file_filter

    def _run_loader(self, filename, app_id, auto=False):
        path = str(Path(filename).expanduser().resolve())
        if not Path(path).is_file():
            self.status.set_text("No se encontró el paquete seleccionado."); return
        self.status.set_text("Instalando… Nexus OmniLoader está procesando el paquete seleccionado.")
        progress = Gtk.ProgressBar(); progress.set_show_text(True); progress.set_text("Instalando…")
        self.content.pack_start(progress, False, False, 0); self.window.show_all()
        loader = os.environ.get("NEXUS_OMNILOADER", "/usr/bin/nexus-omniloader")
        try:
            log = tempfile.TemporaryFile(mode="w+t")
            process = subprocess.Popen([loader, path], stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, text=True, close_fds=True)
        except OSError as exc:
            progress.destroy(); self.status.set_text(f"No se pudo iniciar OmniLoader: {exc}"); return
        # OmniLoader does not expose fractional progress; show an honest live pulse
        # while the child runs, then record success only on its zero exit status.
        def poll():
            code = process.poll()
            if code is None:
                progress.pulse(); return True
            log.seek(0)
            output = log.read().strip()
            log.close()
            progress.destroy()
            if code == 0:
                self.installed[app_id] = path; self._save_installed()
                self.status.set_text(f"Instalado ✓  {Path(path).name}")
                self._render()
                if auto: GLib.timeout_add(300, lambda: self._run_loader(path, app_id, auto=False) or False)
            else:
                detail = output[-180:] if output else f"OmniLoader terminó con código {code}."
                self.status.set_text(f"Instalación no completada: {detail}")
            return False
        GLib.timeout_add(140, poll)

    def run(self):
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
            else:
                GLib.timeout_add(250, lambda: self._install_clicked(None, found) or False)
        Gtk.main()


def main():
    parser = argparse.ArgumentParser(description="Nexus OmniStore")
    parser.add_argument("--select-tab", choices=[section[0] for section in SECTIONS], default="windows")
    parser.add_argument("--install-app", help="Instala una aplicación del catálogo por identificador")
    parser.add_argument("--package-path", help="Ruta local del paquete para automatización (opcional)")
    parser.add_argument("--auto-launch", action="store_true", help="Abre el paquete al terminar una instalación correcta")
    args = parser.parse_args()
    OmniStore(args).run()


if __name__ == "__main__":
    main()
