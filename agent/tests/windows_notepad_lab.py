"""Actual Notepad++ install/edit/save probe; disposable Debian/Wine/Xvfb only."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.request
from PIL import ImageGrab

URL = 'https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.9.8.1/npp.8.9.8.1.Installer.x64.exe'
SHA256 = '26f3bcced788fadbac4e7e577b430ea2ce6060cf3bcad993ef4612ecd7d743da'
evidence = Path('windows-evidence').resolve()
evidence.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='nexus-notepad-lab-') as directory:
    root = Path(directory)
    setup = root / 'Notepad Windows installer.exe'
    with urllib.request.urlopen(URL, timeout=60) as response:
        payload = response.read(32 * 1024 * 1024 + 1)
    assert hashlib.sha256(payload).hexdigest() == SHA256, 'Official pinned installer digest mismatch'
    setup.write_bytes(payload)
    env = dict(os.environ, WINEPREFIX=str(root / 'prefix'), WINEARCH='win64',
               WINEDLLOVERRIDES='mscoree,mshtml=', WINEDEBUG='-all')
    binary = root / 'prefix/drive_c/Program Files/Notepad++/notepad++.exe'
    sample = root / 'Nexus sample.txt'
    sample.write_text('initial sample', encoding='utf-8')
    expected = 'Nexus Windows compatibility test: saved from Notepad++.'
    try:
        with (evidence / 'notepad-install.log').open('w') as log:
            subprocess.run(['wine', str(setup), '/S', '/noUpdater'], env=env,
                           stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                           timeout=180, check=True)
        assert binary.is_file(), 'Expected installed Windows executable missing'
        windows_path = subprocess.check_output(['winepath', '-w', str(sample)], env=env, text=True).strip()
        with (evidence / 'notepad-gui.log').open('w') as log:
            subprocess.Popen(['wine', str(binary), '-multiInst', '-nosession', '-noPlugin', windows_path],
                             env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log)
        deadline = time.monotonic() + 45
        window = None
        while time.monotonic() < deadline:
            result = subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', 'Nexus sample.txt'],
                                    text=True, capture_output=True)
            if result.returncode == 0 and result.stdout.strip():
                window = result.stdout.splitlines()[-1]
                break
            time.sleep(0.3)
        assert window, 'Notepad++ document window absent'
        subprocess.run(['xdotool', 'windowfocus', '--sync', window], check=True, timeout=10)
        subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+a'], check=True)
        subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '10', expected], check=True)
        subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+s'], check=True)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and sample.read_text(encoding='utf-8-sig') != expected:
            time.sleep(0.2)
        assert sample.read_text(encoding='utf-8-sig') == expected, 'GUI did not save exact expected text'
        windows = subprocess.check_output(['xwininfo', '-root', '-tree'], text=True)
        assert 'Notepad++' in windows
        shutil.copyfile(sample, evidence / 'notepad-saved-sample.txt')
        (evidence / 'notepad-windows.txt').write_text(windows)
        ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save(evidence / 'notepad-edit-save.png')
        (evidence / 'notepad-result.txt').write_text(
            'PASS: official pinned Notepad++8.9.8.1 x64 installed using Wine; real GUI opened spaced filename; keyboard editing and Ctrl+S produced exact expected file content.\n'
            'Scope: Debian13/Wine/Xvfb, not Nexus ISO or graphical installer adapter.\n'
            f'Installer SHA256: {SHA256}\n')
    finally:
        subprocess.run(['wineserver', '-k'], env=env, check=False)
