"""Exercise installed desktop/MIME routing under an isolated Debian/Xvfb user."""
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import urllib.request
from PIL import ImageGrab

EXPECTED = 'd54bf805f9f3704d1e8db2fa3498ae7ef2df0312b40b558e7c71c734430a665d'
evidence = Path('windows-evidence').resolve()
with tempfile.TemporaryDirectory(prefix='nexus-mime-lab-') as directory:
    home = Path(directory)
    config = home / '.config'
    config.mkdir()
    (config / 'mimeapps.list').write_bytes(Path('/etc/skel/.config/mimeapps.list').read_bytes())
    setup = home / 'Downloads' / '7zip Windows installer con espacios.exe'
    setup.parent.mkdir()
    with urllib.request.urlopen('https://github.com/ip7z/7zip/releases/download/26.04/7z2604-x64.exe', timeout=60) as response:
        payload = response.read(32 * 1024 * 1024 + 1)
    assert hashlib.sha256(payload).hexdigest() == EXPECTED
    setup.write_bytes(payload)
    env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(config), XDG_DATA_HOME=str(home / '.local/share'))
    mime = subprocess.check_output(['xdg-mime', 'query', 'filetype', str(setup)], env=env, text=True).strip()
    handler = subprocess.check_output(['xdg-mime', 'query', 'default', mime], env=env, text=True).strip()
    assert handler == 'nexus-app-install.desktop', (mime, handler)
    children = []
    try:
        subprocess.run(['gio', 'open', str(setup)], env=env, check=True, timeout=30)
        deadline = time.monotonic() + 30
        windows = ''
        while time.monotonic() < deadline:
            children = []
            for proc in Path('/proc').iterdir():
                if not proc.name.isdigit():
                    continue
                try:
                    argv = (proc / 'cmdline').read_bytes().split(b'\0')
                    if b'/opt/nexus/agent/app_installer.py' in argv and os.fsencode(setup) in argv:
                        children.append(int(proc.name))
                except (FileNotFoundError, PermissionError, ProcessLookupError):
                    pass
            windows = subprocess.check_output(['xwininfo', '-root', '-tree'], text=True)
            if children and 'Nexus Install' in windows:
                break
            time.sleep(0.2)
        assert children and 'Nexus Install' in windows, 'Desktop entry did not launch assistant with exact file argument'
        time.sleep(3)
        assert not list(home.rglob('prefix')), 'Opening a file must not start Windows installation'
        assert not (home / '.wine').exists(), 'Opening a file must not initialize Wine'
        ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save(evidence / 'file-association.png')
        (evidence / 'file-association-result.txt').write_text(
            f'PASS: MIME {mime} selects {handler}; GIO launched actual assistant with exact spaced filename; no Wine prefix before confirmation.\n'
            'Scope: Debian/Xvfb desktop association, not a Thunar click or a Nexus ISO boot.\n' + windows)
    finally:
        for pid in children:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
