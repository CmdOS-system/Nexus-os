"""Exercise both approved Windows apps inside a disposable Nexus Live VM."""
import hashlib
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
sys.path.insert(0, '/opt/nexus/agent')
from app_installer import App, Installer, package_specs


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


cases = [
    ('7zip', 'https://github.com/ip7z/7zip/releases/download/26.04/7z2604-x64.exe', '7-Zip', 'NEXUS_WINDOWS_ISO'),
    ('notepadpp', 'https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.9.8.1/npp.8.9.8.1.Installer.x64.exe', 'Notepad++', 'NEXUS_NOTEPAD_ISO'),
]
seven_receipt = None
for package_id, url, title, marker in cases:
    setup = Path.home() / ('Downloads/' + package_id + ' Windows installer.exe')
    setup.parent.mkdir(exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = response.read(32 * 1024 * 1024 + 1)
    assert hashlib.sha256(payload).hexdigest() == package_specs()[package_id]['sha256']
    setup.write_bytes(payload)
    mime = subprocess.check_output(['xdg-mime', 'query', 'filetype', str(setup)], text=True).strip()
    handler = subprocess.check_output(['xdg-mime', 'query', 'default', mime], text=True).strip()
    assert handler == 'nexus-app-install.desktop', (mime, handler)
    service = Installer(package_id=package_id)
    assert not (service.root / 'prefix').exists(), 'Fresh disposable Live profile required'
    app = App(service)
    try:
        app.select_path(setup)
        wait(app, lambda: not app.busy)
        assert service.ready and service.package_id == package_id, app.status.get()
        assert not (service.root / 'prefix').exists()
        print(marker + '_PREPARED', flush=True)
        hold(app, 10)
        app.confirm.invoke()
        wait(app, lambda: not app.busy)
        assert service.installed, app.status.get()
        app.open_button.invoke()
        hold(app, 12)
        windows = subprocess.check_output(['xwininfo', '-root', '-tree'], text=True)
        assert title in windows, windows
        print(windows, flush=True)
        print(marker + '_OPEN', flush=True)
        hold(app, 10)
        entry = service.menu_entry()
        assert entry.is_file()
        subprocess.run(['wineserver', '-k'], env=service.environment(), check=False)
        app.request_close()
        app = None
        subprocess.run(['gio', 'launch', str(entry)], check=True, timeout=30)
        time.sleep(12)
        windows = subprocess.check_output(['xwininfo', '-root', '-tree'], text=True)
        assert title in windows and 'Nexus Install' not in windows, windows
        print(marker + '_MENU_PASS', flush=True)
        receipt = service.root / 'install-receipt.json'
        if package_id == '7zip':
            seven_receipt = (receipt, receipt.read_bytes())
        else:
            assert seven_receipt[0].read_bytes() == seven_receipt[1]
    finally:
        subprocess.run(['wineserver', '-k'], env=service.environment(), check=False)
        if app is not None:
            app.request_close()
print('NEXUS_WINDOWS_ISO_PASS', flush=True)
