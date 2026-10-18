"""Exercise a diskless KVM VM in the explicitly opted-in disposable CI lab.

No Windows installation, guest OS or Office compatibility is claimed.
"""
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time


def main():
    if os.environ.get('NEXUS_DISPOSABLE_VM_LAB') != '1':
        raise RuntimeError('This VM smoke requires an explicitly disposable laboratory')
    evidence = Path('windows-vm-evidence').resolve()
    evidence.mkdir(exist_ok=True)
    result = {'scope': 'diskless_KVM_engine_only', 'passed': False,
              'windows_installed': False, 'word_validated': False}
    with tempfile.TemporaryDirectory(prefix='nexus-kvm-smoke-') as directory:
        socket_path = Path(directory) / 'qmp.sock'
        process = None
        try:
            result['qemu_version'] = subprocess.check_output(
                ['qemu-system-x86_64', '--version'], text=True, timeout=10).splitlines()[0]
            freerdp = subprocess.run(['xfreerdp3', '/version'], text=True,
                                    capture_output=True, check=True, timeout=10)
            result['freerdp_version'] = (freerdp.stdout + freerdp.stderr).strip()
            if not re.search(r'\b3\.\d', result['freerdp_version']):
                raise RuntimeError('FreeRDP major version3 was not confirmed')
            with (evidence / 'qemu.log').open('w') as log:
                process = subprocess.Popen(
                    ['qemu-system-x86_64', '-no-user-config', '-nodefaults',
                     '-machine', 'q35,accel=kvm', '-cpu', 'host', '-m', '256', '-smp', '1',
                     '-S', '-display', 'none', '-serial', 'none', '-monitor', 'none',
                     '-nic', 'none', '-qmp', f'unix:{socket_path},server=on,wait=off'],
                    stdin=subprocess.DEVNULL, stdout=log, stderr=log)
                end = time.monotonic() + 15
                while not socket_path.exists():
                    if process.poll() is not None:
                        raise RuntimeError(f'QEMU exited before QMP: {process.returncode}')
                    if time.monotonic() >= end:
                        raise RuntimeError('QMP socket absent')
                    time.sleep(0.1)
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                    client.settimeout(5)
                    client.connect(str(socket_path))
                    with client.makefile('rb') as stream:
                        greeting = json.loads(stream.readline(1048576))
                        if 'QMP' not in greeting:
                            raise RuntimeError('Invalid QMP greeting')
                        request_id = 0

                        def command(name):
                            nonlocal request_id
                            request_id += 1
                            client.sendall((json.dumps({'execute': name, 'id': request_id}) + '\n').encode())
                            for _ in range(100):
                                line = stream.readline(1048576)
                                if not line:
                                    raise RuntimeError('QMP closed without matching response')
                                response = json.loads(line)
                                if response.get('id') == request_id:
                                    if 'error' in response or 'return' not in response:
                                        raise RuntimeError(f'QMP {name} failed: {response}')
                                    return response['return']
                            raise RuntimeError('Too many unrelated QMP messages')

                        command('qmp_capabilities')
                        result['kvm'] = command('query-kvm')
                        if result['kvm'].get('enabled') not in (True, 'kvm'):
                            raise RuntimeError('QEMU did not enable KVM acceleration')
                        command('cont')
                        time.sleep(1)
                        result['running'] = command('query-status')
                        if not result['running'].get('running'):
                            raise RuntimeError('Virtual CPU did not enter running state')
                        command('stop')
                        result['stopped'] = command('query-status')
                        if result['stopped'].get('running'):
                            raise RuntimeError('Virtual CPU did not stop')
                        command('quit')
                process.wait(timeout=10)
                if process.returncode != 0:
                    raise RuntimeError(f'QEMU did not exit cleanly: {process.returncode}')
            result['passed'] = True
        except Exception as error:
            result['error'] = str(error)
            raise
        finally:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            (evidence / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
