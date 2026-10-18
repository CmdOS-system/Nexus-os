"""Attempt official Microsoft 365 Word installation/task in disposable Debian/Wine.

This is a diagnostic lab, never a Nexus compatibility claim by itself.
No activation keys or account credentials are supplied, collected or bypassed.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.request
import zipfile
from xml.etree import ElementTree as ET
from PIL import ImageGrab

ODT_URL = 'https://download.microsoft.com/download/6c1eeb25-cf8b-41d9-8d0d-cc1dbc032140/officedeploymenttool_20326-20112.exe'
ODT_SHA256 = 'fbb64358fd4168acd52ee4efe47ffd032b6231dfb415ae2dce61b0e58ba67f86'
EXPECTED = 'Nexus Word desktop test: edited and saved.'


def main():
    if os.geteuid() == 0:
        raise RuntimeError('Run Office lab as an unprivileged disposable user')
    evidence = Path('office-evidence').resolve()
    evidence.mkdir(exist_ok=True)
    result = {'scope': 'Debian13/Wine/Xvfb laboratory; not Nexus ISO',
              'product': 'Microsoft 365 Apps for enterprise, Current, 32-bit, en-us',
              'odt_version': '16.0.20326.20112', 'odt_sha256': ODT_SHA256,
              'stage': 'prepare', 'installed': False, 'word_task_passed': False}
    with tempfile.TemporaryDirectory(prefix='nexus-office-') as directory:
        root = Path(directory)
        env = dict(os.environ, WINEPREFIX=str(root / 'prefix'), WINEARCH='win64',
                   WINEDLLOVERRIDES='mscoree,mshtml,winemenubuilder.exe=',
                   WINEDEBUG='-all,err+all,warn+seh')

        def run(stage, args, timeout):
            result['stage'] = stage
            with (evidence / (stage + '.log')).open('w') as log:
                subprocess.run(args, env=env, cwd=root, stdin=subprocess.DEVNULL,
                               stdout=log, stderr=log, check=True, timeout=timeout)

        def screenshot(name):
            ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save(evidence / name)

        def collect_diagnostics():
            for label, command in [('processes', ['ps', '-eo', 'pid,etimes,args']),
                                   ('windows', ['xwininfo', '-root', '-tree']),
                                   ('clicktorun-service', ['wine', 'sc', 'query', 'ClickToRunSvc'])]:
                try:
                    output = subprocess.run(command, env=env, text=True, errors='replace',
                                            capture_output=True, timeout=10)
                    (evidence / (label + '.txt')).write_text(
                        (output.stdout + output.stderr)[-262144:], encoding='utf-8')
                except Exception as error:
                    (evidence / (label + '.txt')).write_text(str(error), encoding='utf-8')
            # Microsoft directs ODT troubleshooting to user/system TEMP logs.
            users = root / 'prefix/drive_c/users'
            locations = [root / 'prefix/drive_c/windows/temp']
            if users.is_dir():
                for user in users.iterdir():
                    locations.extend([user / 'AppData/Local/Temp', user / 'Temp'])
            exported = []
            for location in locations:
                if not location.is_dir():
                    continue
                for path in sorted(location.rglob('*')):
                    if len(exported) >= 24:
                        break
                    if path.is_symlink() or not path.is_file() or path.suffix.lower() not in ('.log', '.txt'):
                        continue
                    if not path.resolve().is_relative_to(root.resolve()):
                        continue
                    with path.open('rb') as source:
                        source.seek(max(0, path.stat().st_size - 262144))
                        tail = source.read(262144)
                    name = f'office-temp-{len(exported):02}.log'
                    (evidence / name).write_bytes(tail)
                    exported.append({'source': str(path.relative_to(root)), 'artifact': name})
            (evidence / 'temp-log-index.json').write_text(json.dumps(exported, indent=2))

        def word_window(label, seconds=90):
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                found = subprocess.run(['xdotool', 'search', '--onlyvisible', '--name', label],
                                       text=True, capture_output=True)
                if found.returncode == 0 and found.stdout.strip():
                    return found.stdout.splitlines()[-1]
                time.sleep(0.5)
            raise RuntimeError('Word document window absent; inspect failure screenshot')

        try:
            # Wine's msv1_0 package requires ntlm_auth before it can register NTLM.
            # Check before wineboot so an incomplete SSPI setup cannot hide as a
            # long Office setup timeout. No credentials are supplied to this check.
            result['stage'] = 'ntlm-helper-preflight'
            result['ntlm_auth_version'] = subprocess.check_output(
                ['ntlm_auth', '--version'], text=True, timeout=10).strip()
            result['wine_version'] = subprocess.check_output(['wine', '--version'], text=True).strip()
            result['stage'] = 'download-official-odt'
            with urllib.request.urlopen(ODT_URL, timeout=60) as response:
                data = response.read(16 * 1024 * 1024 + 1)
            if hashlib.sha256(data).hexdigest() != ODT_SHA256:
                raise RuntimeError('Official pinned ODT digest mismatch')
            odt = root / 'odt.exe'
            odt.write_bytes(data)
            toolkit = root / 'toolkit'
            run('wine-initialize', ['wine', 'wineboot', '--init'], 300)
            windows_toolkit = subprocess.check_output(['winepath', '-w', str(toolkit)], env=env, text=True).strip()
            # Use Microsoft's own self-extractor. Its embedded Usage text defines
            # /quiet and /extract:path; generic 7z failed on the SFX file attributes.
            run('extract-odt', ['wine', str(odt), '/quiet', '/extract:' + windows_toolkit], 120)
            setup = next(toolkit.rglob('setup.exe'), None)
            if setup is None:
                raise RuntimeError('ODT archive did not contain setup.exe')
            result['setup_sha256'] = hashlib.sha256(setup.read_bytes()).hexdigest()
            config = root / 'configuration.xml'
            config.write_text('''<Configuration>
 <Add OfficeClientEdition="32" Channel="Current" Version="16.0.20430.20182">
  <Product ID="O365ProPlusRetail"><Language ID="en-us"/>
   <ExcludeApp ID="Access"/><ExcludeApp ID="Excel"/><ExcludeApp ID="Groove"/>
   <ExcludeApp ID="Lync"/><ExcludeApp ID="OneDrive"/><ExcludeApp ID="OneNote"/>
   <ExcludeApp ID="Outlook"/><ExcludeApp ID="PowerPoint"/>
   <ExcludeApp ID="Publisher"/><ExcludeApp ID="Teams"/>
  </Product>
 </Add>
 <Display Level="Full" AcceptEULA="TRUE"/>
</Configuration>''', encoding='utf-8')
            payload = root / 'payload'
            windows_payload = subprocess.check_output(['winepath', '-w', str(payload)], env=env, text=True).strip()
            configuration = ET.parse(config)
            configuration.find('Add').set('SourcePath', windows_payload)
            configuration.write(config, encoding='utf-8', xml_declaration=True)
            # This setup belongs only to a temporary lab profile; no OS root access.
            windows_config = subprocess.check_output(['winepath', '-w', str(config)], env=env, text=True).strip()
            # Keep total installation budget at 720 seconds; isolate CDN download
            # from local installation instead of extending the previous timeout.
            run('office-download', ['wine', str(setup), '/download', windows_config], 360)
            versions = payload / 'Office/Data'
            if not versions.is_dir() or not any(versions.iterdir()):
                raise RuntimeError('ODT download returned without Office payload evidence')
            result['download_entries'] = sorted(path.name for path in versions.iterdir())
            run('office-configure', ['wine', str(setup), '/configure', windows_config], 360)
            binaries = [p for p in (root / 'prefix/drive_c').rglob('*')
                        if p.is_file() and p.name.lower() == 'winword.exe']
            if len(binaries) != 1:
                raise RuntimeError('Office setup did not produce one identifiable WINWORD.EXE')
            result['installed'] = True
            result['word_binary_sha256'] = hashlib.sha256(binaries[0].read_bytes()).hexdigest()
            sample = root / 'Nexus Word sample.docx'
            with zipfile.ZipFile(sample, 'w', zipfile.ZIP_DEFLATED) as doc:
                doc.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
                doc.writestr('_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
                doc.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Nexus initial text.</w:t></w:r></w:p><w:sectPr/></w:body></w:document>')
            windows_sample = subprocess.check_output(['winepath', '-w', str(sample)], env=env, text=True).strip()
            result['stage'] = 'word-edit-save'
            with (evidence / 'word-launch.log').open('w') as log:
                subprocess.Popen(['wine', str(binaries[0]), '/q', windows_sample], env=env,
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log)
            window = word_window('Nexus Word sample')
            subprocess.run(['xdotool', 'windowfocus', '--sync', window], check=True, timeout=10)
            subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+End', 'Return'], check=True)
            subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '10', EXPECTED], check=True)
            subprocess.run(['xdotool', 'key', '--clearmodifiers', 'ctrl+s'], check=True)
            end = time.monotonic() + 30
            while time.monotonic() < end:
                with zipfile.ZipFile(sample) as doc:
                    text = ''.join(ET.fromstring(doc.read('word/document.xml')).itertext())
                if EXPECTED in text:
                    break
                time.sleep(0.5)
            else:
                raise RuntimeError('Real Word GUI did not save the expected text; activation or UI may block editing')
            screenshot('word-edit-save.png')
            run('wine-stop-before-reopen', ['wineserver', '-k'], 20)
            run('wine-wait-before-reopen', ['wineserver', '-w'], 30)
            result['stage'] = 'word-reopen'
            with (evidence / 'word-reopen.log').open('w') as log:
                subprocess.Popen(['wine', str(binaries[0]), '/q', windows_sample], env=env,
                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log)
            word_window('Nexus Word sample')
            time.sleep(3)
            screenshot('word-reopened.png')
            (evidence / 'word-saved-sample.docx').write_bytes(sample.read_bytes())
            result.update(stage='complete', word_task_passed=True)
        except Exception as error:
            result['error'] = str(error)
            try:
                screenshot('office-failure.png')
            except Exception:
                pass
            raise
        finally:
            try:
                collect_diagnostics()
            except Exception as error:
                result['diagnostic_error'] = str(error)
            # No keys, credentials, installer binaries or complete Wine profile in artifacts.
            (evidence / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
            subprocess.run(['wineserver', '-k'], env=env, check=False, timeout=20)


if __name__ == '__main__':
    main()
