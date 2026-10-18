"""Read-only local prerequisites for a future Windows/Office VM laboratory.

No VM creation, package installation, permission changes or license checks.
Prerequisites are not evidence that Windows, RemoteApp or Word works.
"""
import fcntl
import json
import os
from pathlib import Path
import platform
import shutil

KVM_GET_API_VERSION = 0xAE00


def check_kvm(device='/dev/kvm'):
    try:
        descriptor = os.open(device, os.O_RDWR | os.O_CLOEXEC)
    except FileNotFoundError:
        return {'status': 'missing', 'available': False}
    except PermissionError:
        return {'status': 'permission_denied', 'available': False}
    except OSError as error:
        return {'status': 'open_error', 'available': False, 'errno': error.errno}
    try:
        version = fcntl.ioctl(descriptor, KVM_GET_API_VERSION, 0)
        return {'status': 'api_available' if version == 12 else 'unsupported_api',
                'available': version == 12, 'api_version': version}
    except OSError as error:
        return {'status': 'ioctl_error', 'available': False, 'errno': error.errno}
    finally:
        os.close(descriptor)


def memory_info(path='/proc/meminfo'):
    result = {}
    try:
        for line in Path(path).read_text().splitlines():
            name, _, value = line.partition(':')
            if name in ('MemTotal', 'MemAvailable'):
                result[name] = int(value.split()[0]) * 1024
    except (OSError, ValueError, IndexError):
        return {'status': 'unknown'}
    return {'status': 'observed', **result}


def collect():
    names = ('qemu-system-x86_64', 'virsh', 'docker', 'podman', 'xfreerdp3', 'xfreerdp')
    commands = {name: shutil.which(name) is not None for name in names}
    kvm = check_kvm()
    try:
        disk = {'status': 'observed', 'free_bytes': shutil.disk_usage(Path.home()).free}
    except OSError:
        disk = {'status': 'unknown'}
    # Presence of an executable does not prove an enabled daemon or its version.
    missing = []
    if platform.machine().lower() not in ('x86_64', 'amd64'):
        missing.append('x86_64_host_for_initial_windows_x64_plan')
    if not kvm['available']:
        missing.append('accessible_kvm_api_12')
    if not commands['qemu-system-x86_64']:
        missing.append('qemu_executable')
    if not any(commands[name] for name in ('virsh', 'docker', 'podman')):
        missing.append('vm_manager_executable')
    if not (commands['xfreerdp3'] or commands['xfreerdp']):
        missing.append('freerdp_executable_version_3_requires_validation')
    return {'scope': 'read_only_prerequisites_not_office_compatibility',
            'architecture': platform.machine(), 'kvm': kvm, 'memory': memory_info(),
            'home_filesystem': disk, 'commands_present': commands, 'missing': missing,
            'static_prerequisites_detected': not missing,
            'word_validated': False, 'windows_installation_verified': False,
            'remaining': ['confirm_freerdp_3_and_vm_manager_access',
                          'review_memory_and_storage_budget',
                          'supply_legitimate_windows_and_office_entitlements',
                          'install_windows_and_word_in_disposable_virtual_disk',
                          'validate_remoteapp_and_word_document_task_in_nexus']}


if __name__ == '__main__':
    print(json.dumps(collect(), indent=2))
