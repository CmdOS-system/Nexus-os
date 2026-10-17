"""Run only inside a disposable Nexus Live VM using its packaged runtime."""
import hashlib
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
sys.path.insert(0, '/opt/nexus/agent')
from app_installer import App, Installer


def wait(app, condition, seconds=230):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.update()
        if condition():
            return
        time.sleep(0.1)
    raise RuntimeError('GUI timeout: ' + app.status.get())


def hold(app, seconds):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.update()
        time.sleep(0.1)


setup = Path.home() / 'Downloads/7zip Windows installer.exe'
setup.parent.mkdir(exist_ok=True)
with urllib.request.urlopen('https://github.com/ip7z/7zip/releases/download/26.04/7z2604-x64.exe', timeout=60) as response:
    payload = response.read(32 * 1024 * 1024 + 1)
assert hashlib.sha256(payload).hexdigest() == 'd54bf805f9f3704d1e8db2fa3498ae7ef2df0312b40b558e7c71c734430a665d'
setup.write_bytes(payload)
mime = subprocess.check_output(['xdg-mime', 'query', 'filetype', str(setup)], text=True).strip()
handler = subprocess.check_output(['xdg-mime', 'query', 'default', mime], text=True).strip()
assert handler == 'nexus-app-install.desktop', (mime, handler)
service = Installer()
assert not (service.root / 'prefix').exists(), 'Probe requires fresh disposable Live profile'
app = App(service)
try:
    app.select_path(setup)
    wait(app, lambda: not app.busy)
    assert service.ready, app.status.get()
    assert not (service.root / 'prefix').exists()
    print('NEXUS_WINDOWS_ISO_PREPARED', flush=True)
    hold(app, 10)
    app.confirm.invoke()
    wait(app, lambda: not app.busy)
    assert service.installed, app.status.get()
    app.open_button.invoke()
    hold(app, 12)
    windows = subprocess.check_output(['xwininfo', '-root', '-tree'], text=True)
    assert '7-Zip' in windows, windows
    print(windows, flush=True)
    print('NEXUS_WINDOWS_ISO_OPEN', flush=True)
    hold(app, 10)
    print('NEXUS_WINDOWS_ISO_PASS', flush=True)
finally:
    subprocess.run(['wineserver', '-k'], env=service.environment(), check=False)
    app.request_close()
