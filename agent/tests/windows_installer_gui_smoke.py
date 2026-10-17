"""Real GUI install flow, isolated Debian user. Never attach to an active desktop."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request
from PIL import ImageGrab
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app_installer import App, Installer


def wait_until(app, condition, seconds=200):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        app.update()
        if condition():
            return
        time.sleep(0.1)
    raise AssertionError('GUI did not reach expected state: ' + app.status.get())


with tempfile.TemporaryDirectory(prefix='nexus-gui-lab-') as directory:
    root = Path(directory)
    setup = root / '7zip Windows installer.exe'
    with urllib.request.urlopen('https://github.com/ip7z/7zip/releases/download/26.04/7z2604-x64.exe', timeout=60) as response:
        payload = response.read(32 * 1024 * 1024 + 1)
    assert len(payload) <= 32 * 1024 * 1024
    setup.write_bytes(payload)
    service = Installer()
    app = App(service)
    try:
        app.select_path(setup)
        wait_until(app, lambda: not app.busy)
        assert service.ready, app.status.get()
        assert not service.installed
        assert not (service.root / 'prefix').exists(), 'Selecting must not execute the installer'
        app.confirm.invoke()
        wait_until(app, lambda: not app.busy)
        assert service.installed, app.status.get()
        app.open_button.invoke()
        app.update()
        time.sleep(8)
        windows = subprocess.check_output(['xwininfo', '-root', '-tree'], text=True)
        assert '7-Zip' in windows
        assert 'Nexus Install' in windows
        Path('windows-evidence/gui-assistant-windows.txt').write_text(windows)
        ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save('windows-evidence/nexus-install-7zip.png')
        Path('windows-evidence/gui-assistant-result.txt').write_text('PASS: selection verified without execution; graphical confirmation installed; graphical Open created 7-Zip window. No OS reboot or general-format acceptance.\n')
        subprocess.run(['wineserver', '-k'], env=service.environment(), check=False)
        app.request_close()
        service = Installer()
        app = App(service)
        app.update()
        assert service.installed, 'Verified install was not restored after closing assistant'
        assert not app.open_button.instate(['disabled'])
        assert not service.ready, 'Reopening must not prepare or run a new installer'
        app.open_button.invoke()
        app.update()
        time.sleep(8)
        windows = subprocess.check_output(['xwininfo', '-root', '-tree'], text=True)
        assert '7-Zip' in windows
        ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save('windows-evidence/nexus-install-reopened.png')
        Path('windows-evidence/gui-reopen-result.txt').write_text('PASS: closed assistant and Wine; reopened from verified receipt; Open enabled without selecting installer; opened real7-Zip again. This is not a reboot persistence test.\\n')
        subprocess.run(['wineserver', '-k'], env=service.environment(), check=False)
        entry = service.menu_entry()
        assert entry.is_file()
        subprocess.run(['desktop-file-validate', str(entry)], check=True)
        app.request_close()
        app = None
        subprocess.run(['gio', 'launch', str(entry)], check=True, timeout=30)
        time.sleep(12)
        windows = subprocess.check_output(['xwininfo', '-root', '-tree'], text=True)
        assert '7-Zip' in windows, 'Desktop launcher did not open actual Windows application'
        assert 'Nexus Install' not in windows, 'Menu action should open installed application directly'
        ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save('windows-evidence/7zip-menu-launch.png')
        Path('windows-evidence/menu-launch-result.txt').write_text('PASS: generated desktop entry validated; GIO launched installed 7-Zip after assistant and Wine closed. No physical menu click or reboot tested.\n')
        subprocess.run(['wineserver', '-k'], env=service.environment(), check=False)
        seven_root = service.root
        seven_receipt = (seven_root / 'install-receipt.json').read_bytes()
        notepad_setup = root / 'Editor Windows con espacios.exe'
        with urllib.request.urlopen('https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.9.8.1/npp.8.9.8.1.Installer.x64.exe', timeout=60) as response:
            notepad_payload = response.read(32 * 1024 * 1024 + 1)
        assert len(notepad_payload) <= 32 * 1024 * 1024
        notepad_setup.write_bytes(notepad_payload)
        service = Installer()
        app = App(service)
        app.select_path(notepad_setup)
        wait_until(app, lambda: not app.busy)
        assert service.package_id == 'notepadpp' and service.ready, app.status.get()
        assert service.root != seven_root
        assert not (service.root / 'prefix').exists(), 'Selecting Notepad must not run installer'
        assert not app.confirm.instate(['disabled'])
        app.confirm.invoke()
        wait_until(app, lambda: not app.busy)
        assert service.installed, app.status.get()
        assert (seven_root / 'install-receipt.json').read_bytes() == seven_receipt
        app.open_button.invoke()
        app.update()
        time.sleep(10)
        windows = subprocess.check_output(['xwininfo', '-root', '-tree'], text=True)
        assert 'Notepad++' in windows
        ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save('windows-evidence/nexus-notepad-install.png')
        subprocess.run(['wineserver', '-k'], env=service.environment(), check=False)
        entry = service.menu_entry()
        subprocess.run(['desktop-file-validate', str(entry)], check=True)
        app.request_close()
        app = None
        subprocess.run(['gio', 'launch', str(entry)], check=True, timeout=30)
        time.sleep(12)
        windows = subprocess.check_output(['xwininfo', '-root', '-tree'], text=True)
        assert 'Notepad++' in windows
        assert 'Nexus Install' not in windows
        ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save('windows-evidence/notepad-menu-launch.png')
        Path('windows-evidence/notepad-assistant-result.txt').write_text('PASS: graphical selection identified Notepad++ by hash; no execution before confirmation; install/Open and desktop menu action opened actual application; separate 7-Zip receipt unchanged. Debian/Wine laboratory, not ISO.\n')
    finally:
        if app is not None and app.busy:
            wait_until(app, lambda: not app.busy)
        subprocess.run(['wineserver', '-k'], env=service.environment(), check=False)
        if app is not None:
            app.request_close()
