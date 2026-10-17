"""Early Nexus graphical app installer: only a pinned, tested Windows package.

Does not install APK/Linux formats or prepare Wine automatically yet.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import stat
import subprocess
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, ttk

PACKAGE_SHA256 = 'd54bf805f9f3704d1e8db2fa3498ae7ef2df0312b40b558e7c71c734430a665d'
PACKAGE_NAME = '7-Zip 26.04 para Windows x64'
MAX_BYTES = 32 * 1024 * 1024


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
        if digest.hexdigest() != PACKAGE_SHA256:
            raise PackageError('Este prototipo solo admite el instalador oficial de 7-Zip 26.04 x64 verificado.')
        destination.chmod(0o400)
        return digest.hexdigest()
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        os.close(descriptor)


class Installer:
    def __init__(self, data_root=None):
        self.root = Path(data_root) if data_root else Path.home() / '.local/share/nexus/apps/7zip-26.04-x64'
        self.wine = shutil.which('wine')
        self.stage = tempfile.TemporaryDirectory(prefix='nexus-app-')
        self.package = Path(self.stage.name) / 'setup.exe'
        self.ready = False
        self.installed = self.has_verified_installation()

    def binary(self):
        return self.root / 'prefix/drive_c/Program Files/7-Zip/7zFM.exe'

    def has_verified_installation(self):
        try:
            receipt_path = self.root / 'install-receipt.json'
            if receipt_path.stat().st_size > 4096:
                return False
            receipt = json.loads(receipt_path.read_text())
            binary = self.binary()
            if not isinstance(receipt, dict) or not 0 < binary.stat().st_size <= MAX_BYTES:
                return False
            return (receipt.get('package_sha256') == PACKAGE_SHA256
                    and receipt.get('binary_sha256') == hashlib.sha256(binary.read_bytes()).hexdigest())
        except (OSError, ValueError):
            return False

    def record_installation(self):
        receipt = {'package_sha256': PACKAGE_SHA256,
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
        return data_home / 'applications/nexus-7zip.desktop'

    def register_menu_entry(self):
        entry = self.menu_entry()
        entry.parent.mkdir(parents=True, exist_ok=True)
        content = ('[Desktop Entry]\nType=Application\nName=7-Zip (Windows)\n'
                   'Comment=Abrir 7-Zip instalado con Nexus Install\n'
                   'Exec=/usr/bin/python3 /opt/nexus/agent/app_installer.py --open-installed\n'
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
        stage_verified(Path(path), self.package)
        self.ready = True

    def environment(self):
        env = os.environ.copy()
        env.update(WINEPREFIX=str(self.root / 'prefix'), WINEARCH='win64',
                   WINEDLLOVERRIDES='mscoree,mshtml=', WINEDEBUG='-all')
        return env

    def install(self):
        if not self.ready:
            raise PackageError('Selecciona y verifica el instalador antes de instalar.')
        if os.geteuid() == 0:
            raise PackageError('La instalación de aplicaciones debe ejecutarse con tu usuario, sin privilegios de administrador.')
        # A downloaded source may change after selection; only the verified
        # private copy is ever launched, and it is checked again at confirmation.
        if hashlib.sha256(self.package.read_bytes()).hexdigest() != PACKAGE_SHA256:
            raise PackageError('El instalador preparado cambió. Selecciónalo de nuevo.')
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock = self.root / 'install.lock'
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise PackageError('Ya hay una instalación en curso en este perfil.') from error
        os.close(fd)
        try:
            with (self.root / 'install.log').open('w') as log:
                subprocess.run([self.wine, str(self.package), '/S'], env=self.environment(),
                               stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                               timeout=180, check=True)
            binary = self.root / 'prefix/drive_c/Program Files/7-Zip/7zFM.exe'
            if not binary.is_file():
                raise PackageError('El instalador terminó, pero no se encontró la aplicación esperada.')
            self.record_installation()
            self.register_menu_entry()
            self.installed = True
        finally:
            lock.unlink(missing_ok=True)

    def launch(self):
        if not self.installed or not self.has_verified_installation():
            self.installed = False
            raise PackageError('No se encontró una instalación verificada. Instala de nuevo el paquete aprobado.')
        if not self.wine:
            raise PackageError('Wine no está disponible para abrir la aplicación.')
        binary = self.root / 'prefix/drive_c/Program Files/7-Zip/7zFM.exe'
        return subprocess.Popen([self.wine, str(binary)], env=self.environment(),
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, close_fds=True)

    def close(self):
        self.stage.cleanup()


class App(tk.Tk):
    def __init__(self, installer=None):
        super().__init__()
        self.service = installer or Installer()
        self.events = queue.Queue()
        self.busy = False
        self.title('Nexus Install — Aplicaciones')
        self.geometry('700x390')
        frame = ttk.Frame(self, padding=24)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Instalar una aplicación', font=('Sans', 21, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='Primer prototipo: 7-Zip 26.04 para Windows x64.\nAPK y paquetes Linux: integración pendiente.').pack(anchor='w', pady=14)
        self.status = tk.StringVar(value='Selecciona el instalador descargado desde el sitio oficial de 7-Zip.')
        ttk.Label(frame, textvariable=self.status, wraplength=640).pack(anchor='w', pady=10)
        self.choose = ttk.Button(frame, text='Seleccionar archivo…', command=self.select)
        self.choose.pack(anchor='w')
        self.confirm = ttk.Button(frame, text='Instalar 7-Zip en mi perfil', command=self.confirm_install, state='disabled')
        self.confirm.pack(anchor='w', pady=10)
        self.open_button = ttk.Button(frame, text='Abrir 7-Zip', command=self.open_app, state='disabled')
        self.open_button.pack(anchor='w')
        if self.service.installed:
            self.status.set('7-Zip ya está instalado en tu perfil. Puedes abrirlo sin reinstalar.')
            self.open_button.state(['!disabled'])
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=14)
        self.protocol('WM_DELETE_WINDOW', self.request_close)
        self.after(100, self.poll)

    def work(self, action, success):
        if self.busy:
            return
        self.busy = True
        self.choose.state(['disabled'])
        self.confirm.state(['disabled'])
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
        self.work(lambda: self.service.prepare(path), 'Verificado: ' + PACKAGE_NAME + '. Pulsa Instalar para autorizar su instalación en tu perfil.')

    def confirm_install(self):
        self.status.set('Instalando en un perfil Windows separado. Espera a que termine…')
        self.work(self.service.install, 'Instalación finalizada. Ya puedes abrir 7-Zip.')

    def poll(self):
        try:
            ok, message = self.events.get_nowait()
            self.busy = False
            self.progress.stop()
            self.status.set(message if ok else 'No se pudo completar: ' + message)
            self.choose.state(['!disabled'])
            if ok and self.service.ready and not self.service.installed:
                self.confirm.state(['!disabled'])
            if self.service.installed:
                self.open_button.state(['!disabled'])
        except queue.Empty:
            pass
        self.after(100, self.poll)

    def open_app(self):
        try:
            self.service.launch()
            self.status.set('Se inició 7-Zip. Comprueba su ventana.')
        except Exception as error:
            self.status.set(str(error))

    def request_close(self):
        if self.busy:
            self.status.set('Hay una operación en curso. Espera a que termine para cerrar.')
            return
        self.service.close()
        self.destroy()


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description='Nexus Install')
    parser.add_argument('package', nargs='?')
    parser.add_argument('--open-installed', action='store_true')
    args = parser.parse_args(argv)
    if args.open_installed and args.package:
        parser.error('No se combina abrir una aplicación con seleccionar un instalador.')
    service = Installer()
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
