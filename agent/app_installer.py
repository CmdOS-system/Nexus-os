"""Early Nexus graphical app installer: two pinned Windows packages.

Does not install APK/Linux formats yet. Wine must be included in the system.
"""
from __future__ import annotations
import hashlib
import json
import os
import pwd
from pathlib import Path
import queue
import shutil
import stat
import subprocess
import tempfile
import threading
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

PACKAGE_SHA256 = 'd54bf805f9f3704d1e8db2fa3498ae7ef2df0312b40b558e7c71c734430a665d'
PACKAGE_NAME = '7-Zip 26.04 para Windows x64'
MAX_BYTES = 32 * 1024 * 1024


def package_specs():
    return {
        '7zip': {'name': PACKAGE_NAME, 'sha256': PACKAGE_SHA256,
                 'profile': '7zip-26.04-x64', 'binary': 'Program Files/7-Zip/7zFM.exe',
                 'arguments': ['/S'], 'menu_name': '7-Zip (Windows)'},
        'notepadpp': {'name': 'Notepad++ 8.9.8.1 para Windows x64',
                      'sha256': '26f3bcced788fadbac4e7e577b430ea2ce6060cf3bcad993ef4612ecd7d743da',
                      'profile': 'notepadpp-8.9.8.1-x64', 'binary': 'Program Files/Notepad++/notepad++.exe',
                      'arguments': ['/S', '/noUpdater'], 'menu_name': 'Notepad++ (Windows)'},
    }


class PackageError(ValueError):
    pass


def stage_verified(source: Path, destination: Path) -> str:
    """Copy a bounded regular file, then verify copied bytes before execution."""
    descriptor = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_BYTES:
            raise PackageError('El archivo no es un instalador regular admitido.')
        digest = hashlib.sha256()
        total = 0
        with os.fdopen(descriptor, 'rb', closefd=False) as incoming, destination.open('xb') as outgoing:
            while block := incoming.read(1024 * 1024):
                total += len(block)
                if total > MAX_BYTES:
                    raise PackageError('El archivo supera el límite del prototipo.')
                digest.update(block)
                outgoing.write(block)
        if digest.hexdigest() not in {spec['sha256'] for spec in package_specs().values()}:
            raise PackageError('Este prototipo solo admite los instaladores oficiales aprobados de 7-Zip 26.04 x64 y Notepad++ 8.9.8.1 x64.')
        destination.chmod(0o400)
        return digest.hexdigest()
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        os.close(descriptor)


class Installer:
    def __init__(self, data_root=None, package_id='7zip'):
        if package_id not in package_specs():
            raise PackageError('Aplicación no admitida.')
        self.package_id = package_id
        self.root_override = Path(data_root) if data_root is not None else None
        self.root = self.profile_root()
        self.wine = shutil.which('wine')
        self.stage = tempfile.TemporaryDirectory(prefix='nexus-app-')
        self.package = Path(self.stage.name) / 'setup.exe'
        self.ready = False
        self.installed = self.has_verified_installation()

    @property
    def spec(self):
        return package_specs()[self.package_id]

    def profile_root(self):
        return self.root_override if self.root_override is not None else Path.home() / '.local/share/nexus/apps' / self.spec['profile']

    def binary(self):
        return self.root / 'prefix/drive_c' / self.spec['binary']

    def has_verified_installation(self):
        try:
            receipt_path = self.root / 'install-receipt.json'
            if receipt_path.stat().st_size > 4096:
                return False
            receipt = json.loads(receipt_path.read_text())
            binary = self.binary()
            if not isinstance(receipt, dict) or not 0 < binary.stat().st_size <= MAX_BYTES:
                return False
            return (receipt.get('package_sha256') == self.spec['sha256']
                    and receipt.get('binary_sha256') == hashlib.sha256(binary.read_bytes()).hexdigest())
        except (OSError, ValueError):
            return False

    def record_installation(self):
        receipt = {'package_sha256': self.spec['sha256'],
                   'binary_sha256': hashlib.sha256(self.binary().read_bytes()).hexdigest()}
        with tempfile.NamedTemporaryFile(mode='w', dir=self.root, delete=False) as output:
            temporary = Path(output.name)
            json.dump(receipt, output)
        try:
            os.replace(temporary, self.root / 'install-receipt.json')
        finally:
            temporary.unlink(missing_ok=True)

    def menu_entry(self):
        data_home = Path(os.environ.get('XDG_DATA_HOME', ''))
        if not data_home.is_absolute():
            data_home = Path.home() / '.local/share'
        return data_home / 'applications' / ('nexus-' + self.package_id + '.desktop')

    def register_menu_entry(self):
        entry = self.menu_entry()
        entry.parent.mkdir(parents=True, exist_ok=True)
        content = ('[Desktop Entry]\nType=Application\n'
                   f"Name={self.spec['menu_name']}\n"
                   'Comment=Abrir aplicación Windows instalada con Nexus Install\n'
                   'Exec=/usr/bin/python3 /opt/nexus/agent/app_installer.py --open-installed '
                   f'--application {self.package_id}\n'
                   'Icon=application-x-executable\nTerminal=false\nCategories=Utility;\n')
        with tempfile.NamedTemporaryFile(mode='w', dir=entry.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(content)
        try:
            os.replace(temporary, entry)
        finally:
            temporary.unlink(missing_ok=True)

    def prepare(self, path):
        if self.ready:
            raise PackageError('El paquete ya está preparado.')
        if not self.wine:
            raise PackageError('Wine aún no está disponible. La preparación automática del motor está pendiente en este prototipo.')
        digest = stage_verified(Path(path), self.package)
        self.package_id = next(key for key, spec in package_specs().items() if spec['sha256'] == digest)
        self.root = self.profile_root()
        self.installed = self.has_verified_installation()
        self.ready = True

    def environment(self):
        env = os.environ.copy()
        env.update(WINEPREFIX=str(self.root / 'prefix'), WINEARCH='win64',
                   WINEDLLOVERRIDES='mscoree,mshtml,winemenubuilder.exe=', WINEDEBUG='-all')
        return env

    def install(self):
        if not self.ready:
            raise PackageError('Selecciona y verifica el instalador antes de instalar.')
        if os.geteuid() == 0:
            raise PackageError('La instalación de aplicaciones debe ejecutarse con tu usuario, sin privilegios de administrador.')
        # A downloaded source may change after selection; only the verified
        # private copy is ever launched, and it is checked again at confirmation.
        if hashlib.sha256(self.package.read_bytes()).hexdigest() != self.spec['sha256']:
            raise PackageError('El instalador preparado cambió. Selecciónalo de nuevo.')
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock = self.root.parent / ('.' + self.root.name + '.operation.lock')
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise PackageError('Ya hay una instalación en curso en este perfil.') from error
        os.close(fd)
        try:
            with (self.root / 'install.log').open('w') as log:
                ready_marker = self.root / 'wine-ready'
                if not ready_marker.exists() or ready_marker.read_text() != 'win64':
                    log.write('NEXUS_WINE_INIT_BEGIN\n')
                    log.flush()
                    subprocess.run([self.wine, 'wineboot', '--init'], env=self.environment(),
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                   timeout=300, check=True)
                    ready_marker.write_text('win64')
                    log.write('NEXUS_WINE_INIT_END\n')
                log.write('NEXUS_PACKAGE_INSTALL_BEGIN\n')
                log.flush()
                subprocess.run([self.wine, str(self.package), *self.spec['arguments']], env=self.environment(),
                               stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                               timeout=180, check=True)
            binary = self.binary()
            if not binary.is_file():
                raise PackageError('El instalador terminó, pero no se encontró la aplicación esperada.')
            self.apply_compatibility_settings()
            self.record_installation()
            self.register_menu_entry()
            self.installed = True
        finally:
            lock.unlink(missing_ok=True)

    def apply_compatibility_settings(self):
        """Select upstream GDI for the pinned Notepad++ profile, before first launch."""
        if self.package_id != 'notepadpp':
            return
        prefix = self.root / 'prefix'
        username = pwd.getpwuid(os.getuid()).pw_name
        config = prefix / 'drive_c/users' / username / 'AppData/Roaming/Notepad++/config.xml'
        if not config.resolve().is_relative_to(prefix.resolve()):
            raise PackageError('La configuración de la aplicación está fuera de su perfil.')
        if config.exists() and (not config.is_file() or config.is_symlink() or config.stat().st_size > 1024 * 1024):
            raise PackageError('La configuración de la aplicación no es un archivo admitido.')
        try:
            tree = ET.parse(config) if config.exists() else ET.ElementTree(ET.Element('NotepadPlus'))
        except ET.ParseError as error:
            raise PackageError('La configuración de Notepad++ no es válida; se conserva sin sobrescribir.') from error
        if tree.getroot().tag != 'NotepadPlus':
            raise PackageError('La configuración de Notepad++ no tiene el formato esperado.')
        settings = tree.getroot().find('GUIConfigs')
        if settings is None:
            settings = ET.SubElement(tree.getroot(), 'GUIConfigs')
        misc = settings.find("GUIConfig[@name='MISC']")
        if misc is None:
            misc = ET.SubElement(settings, 'GUIConfig', name='MISC')
        misc.set('writeTechnologyEngine', '0')
        config.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=config.parent, delete=False) as output:
            temporary = Path(output.name)
        try:
            tree.write(temporary, encoding='utf-8', xml_declaration=True)
            os.replace(temporary, config)
        finally:
            temporary.unlink(missing_ok=True)

    def launch(self):
        if not self.installed or not self.has_verified_installation():
            self.installed = False
            raise PackageError('No se encontró una instalación verificada. Instala de nuevo el paquete aprobado.')
        if not self.wine:
            raise PackageError('Wine no está disponible para abrir la aplicación.')
        binary = self.binary()
        return subprocess.Popen([self.wine, str(binary)], env=self.environment(),
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, close_fds=True)

    def remove(self):
        if os.geteuid() == 0:
            raise PackageError('Desinstala desde tu usuario, sin privilegios de administrador.')
        if not self.installed or not self.has_verified_installation() or self.root.is_symlink():
            raise PackageError('No se encontró un perfil verificado para desinstalar.')
        gio = shutil.which('gio')
        server = shutil.which('wineserver')
        if not gio or not server:
            raise PackageError('No está disponible la papelera o el control de Wine.')
        lock = self.root.parent / ('.' + self.root.name + '.operation.lock')
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise PackageError('Ya hay una operación en este perfil.') from error
        os.close(fd)
        entry = self.menu_entry()
        saved_entry = None
        try:
            try:
                subprocess.run([server, '-w'], env=self.environment(),
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=5, check=True)
            except subprocess.TimeoutExpired as error:
                raise PackageError('Cierra la aplicación y vuelve a desinstalar; todavía está activa.') from error
            if entry.exists():
                with tempfile.NamedTemporaryFile(dir=self.root, prefix='menu-backup-', suffix='.desktop', delete=False) as output:
                    saved_entry = Path(output.name)
                os.replace(entry, saved_entry)
            try:
                subprocess.run([gio, 'trash', str(self.root)], stdin=subprocess.DEVNULL,
                               capture_output=True, timeout=30, check=True)
                if self.root.exists():
                    raise PackageError('No se pudo confirmar el traslado a la papelera.')
            except Exception:
                if saved_entry is not None and saved_entry.exists():
                    os.replace(saved_entry, entry)
                raise
            self.installed = False
            self.ready = False
            self.package.unlink(missing_ok=True)
        finally:
            lock.unlink(missing_ok=True)

    def close(self):
        self.stage.cleanup()


class App(tk.Tk):
    def __init__(self, installer=None):
        super().__init__()
        self.service = installer or Installer()
        self.events = queue.Queue()
        self.busy = False
        self.title('Nexus Install — Aplicaciones')
        self.geometry('700x470')
        frame = ttk.Frame(self, padding=24)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Instalar una aplicación', font=('Sans', 21, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='Paquetes aprobados: 7-Zip 26.04 y Notepad++ 8.9.8.1 x64.\nAPK y paquetes Linux: integración pendiente.').pack(anchor='w', pady=14)
        self.status = tk.StringVar(value='Selecciona un instalador oficial aprobado de 7-Zip o Notepad++.')
        ttk.Label(frame, textvariable=self.status, wraplength=640).pack(anchor='w', pady=10)
        self.choose = ttk.Button(frame, text='Seleccionar archivo…', command=self.select)
        self.choose.pack(anchor='w')
        self.confirm = ttk.Button(frame, text='Instalar en mi perfil', command=self.confirm_install, state='disabled')
        self.confirm.pack(anchor='w', pady=10)
        self.open_button = ttk.Button(frame, text='Abrir aplicación', command=self.open_app, state='disabled')
        self.open_button.pack(anchor='w')
        self.remove_button = ttk.Button(frame, text='Desinstalar (mover a papelera)', command=self.remove_app, state='disabled')
        self.remove_button.pack(anchor='w', pady=10)
        if self.service.installed:
            self.remove_button.state(['!disabled'])
            self.status.set(self.service.spec['name'] + ' ya está instalado en tu perfil. Puedes abrirlo sin reinstalar.')
            self.open_button.state(['!disabled'])
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=14)
        self.protocol('WM_DELETE_WINDOW', self.request_close)
        self.poll_job = self.after(100, self.poll)

    def work(self, action, success):
        if self.busy:
            return
        self.busy = True
        self.choose.state(['disabled'])
        self.confirm.state(['disabled'])
        self.open_button.state(['disabled'])
        self.remove_button.state(['disabled'])
        self.progress.start()
        def worker():
            try:
                action()
                self.events.put((True, success))
            except Exception as error:
                self.events.put((False, str(error)))
        threading.Thread(target=worker, daemon=True).start()

    def select(self):
        path = filedialog.askopenfilename(title='Seleccionar instalador', filetypes=[('Aplicaciones', '*.exe *.msi *.apk *.deb *.AppImage *.flatpakref'), ('Archivos', '*')])
        if path:
            self.select_path(path)

    def select_path(self, path):
        if self.service.ready:
            self.status.set('Cierra este asistente para elegir otro paquete.')
            return
        self.status.set('Verificando el archivo; todavía no se ejecuta…')
        self.work(lambda: self.service.prepare(path), 'Archivo verificado. Pulsa Instalar para autorizar su instalación en tu perfil.')

    def confirm_install(self):
        self.status.set('Preparando el perfil Windows e instalando la aplicación. Espera a que termine…')
        self.work(self.service.install, 'Instalación finalizada. Ya puedes abrir la aplicación.')

    def poll(self):
        try:
            ok, message = self.events.get_nowait()
            self.busy = False
            self.progress.stop()
            self.status.set(message if ok else 'No se pudo completar: ' + message)
            self.choose.state(['!disabled'])
            self.confirm.configure(text='Instalar ' + self.service.spec['menu_name'])
            self.open_button.configure(text='Abrir ' + self.service.spec['menu_name'])
            if ok and self.service.ready and not self.service.installed:
                self.confirm.state(['!disabled'])
            if self.service.installed:
                self.open_button.state(['!disabled'])
                self.remove_button.state(['!disabled'])
        except queue.Empty:
            pass
        self.poll_job = self.after(100, self.poll)

    def open_app(self):
        try:
            self.service.launch()
            self.status.set('Se inició ' + self.service.spec['name'] + '. Comprueba su ventana.')
        except Exception as error:
            self.status.set(str(error))

    def remove_app(self):
        if self.busy or not self.service.installed:
            return
        if not messagebox.askyesno('Desinstalar aplicación',
                                  'Se moverán a la papelera la aplicación y los archivos guardados dentro de su perfil Windows. '
                                  'Cierra la aplicación antes de continuar. ¿Quieres desinstalarla?',
                                  parent=self, default=messagebox.NO):
            return
        self.status.set('Comprobando que esté cerrada y moviendo el perfil a la papelera…')
        self.work(self.service.remove, 'Aplicación retirada del menú y movida a la papelera. Puedes recuperarla desde allí.')

    def request_close(self):
        if self.busy:
            self.status.set('Hay una operación en curso. Espera a que termine para cerrar.')
            return
        self.after_cancel(self.poll_job)
        self.service.close()
        self.destroy()


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description='Nexus Install')
    parser.add_argument('package', nargs='?')
    parser.add_argument('--open-installed', action='store_true')
    parser.add_argument('--application', choices=tuple(package_specs()), default='7zip')
    args = parser.parse_args(argv)
    if args.open_installed and args.package:
        parser.error('No se combina abrir una aplicación con seleccionar un instalador.')
    service = Installer(package_id=args.application)
    error = None
    if args.open_installed:
        try:
            service.launch()
        except Exception as problem:
            error = str(problem)
        else:
            service.close()
            return 0
    app = App(service)
    if error:
        app.status.set(error)
    elif args.package:
        app.after(100, lambda: app.select_path(args.package))
    app.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
