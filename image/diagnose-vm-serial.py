"""Collect diagnostics through the disposable Live guest's serial login.

Uses the image's public default Live credentials, never host credentials.
No physical disks, system configuration changes, or persistent guest writes.
"""
import argparse
from pathlib import Path
import socket
import threading
import time


def collect(socket_path, log_path):
    deadline = time.monotonic() + 420
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        while True:
            try:
                client.connect(str(socket_path))
                break
            except (FileNotFoundError, ConnectionRefusedError):
                if time.monotonic() >= deadline:
                    raise RuntimeError("Serial socket did not become available")
                time.sleep(0.2)
        client.settimeout(1)
        buffer = bytearray()

        def receive():
            with log_path.open("wb") as output:
                while time.monotonic() < deadline:
                    try:
                        data = client.recv(65536)
                    except socket.timeout:
                        continue
                    except OSError:
                        return
                    if not data:
                        return
                    buffer.extend(data)
                    output.write(data)
                    output.flush()

        thread = threading.Thread(target=receive, daemon=True)
        thread.start()

        def wait_for(needle, seconds=240):
            until = min(deadline, time.monotonic() + seconds)
            while time.monotonic() < until:
                if needle.encode() in buffer:
                    return
                time.sleep(0.2)
            raise RuntimeError(f"Guest serial response absent: {needle}")

        wait_for("login:")
        client.sendall(b"nexus\n")
        wait_for("Password:", 20)
        client.sendall(b"live\n")
        time.sleep(3)
        client.sendall(b"printf 'NEXUS_SERIAL_%s\\n' AUTH_OK\n")
        wait_for("NEXUS_SERIAL_AUTH_OK", 20)
        # A serial login can precede LightDM/XFCE. Earlier diagnostics raced X
        # startup and reported missing authorization before the desktop existed.
        wait_for("NEXUS_XFCE_SESSION_READY_V1")
        time.sleep(10)
        # Fixed read-only diagnostic commands, executed only inside the test guest.
        command = (
            "printf '\\nNEXUS_DIAG_BEGIN\\n'; "
            "id; ps -eo user,pid,args; loginctl list-sessions --no-pager; "
            "sudo -n journalctl -b -u lightdm --no-pager -n 120; "
            "tail -n 160 /home/nexus/.xsession-errors; "
            "sudo -n tail -n 100 /var/log/lightdm/lightdm.log; "
            "sudo -n tail -n 100 /var/log/Xorg.0.log; "
            "export DISPLAY=:0 XAUTHORITY=/home/nexus/.Xauthority; "
            "xrandr --current; xset q; xprop -root _NET_SUPPORTING_WM_CHECK _NET_CLIENT_LIST; "
            "xwininfo -root -tree; printf '\\nNEXUS_DIAG_%s\\n' END\n"
        )
        client.sendall(command.encode())
        wait_for("NEXUS_DIAG_END", 45)
        print("Read-only guest desktop diagnostics collected", flush=True)
        thread.join(timeout=max(0, deadline - time.monotonic()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("socket", type=Path)
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    collect(args.socket, args.log)
