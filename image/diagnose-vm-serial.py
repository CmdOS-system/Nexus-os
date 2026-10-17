"""Collect diagnostics through the disposable Live guest's serial login.

Uses the image's public default Live credentials, never host credentials.
No physical disks or persistent guest writes. Optional Full HD mode changes
only the disposable guest display for screenshots.
"""
import argparse
import base64
from pathlib import Path
import socket
import threading
import time


def collect(socket_path, log_path, full_hd=False):
    deadline = time.monotonic() + 1200
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
        mode_command = (
            "output=$(xrandr --current | awk '$2 == \"connected\" {print $1; exit}'); "
            "if [ -n \"$output\" ]; then xrandr --output \"$output\" --mode 1920x1080; fi; "
        ) if full_hd else ""
        command = (
            "printf '\\nNEXUS_DIAG_BEGIN\\n'; "
            "id; ps -eo user,pid,args; loginctl list-sessions --no-pager; "
            "sudo -n journalctl -b -u lightdm --no-pager -n 120; "
            "tail -n 160 /home/nexus/.xsession-errors; "
            "sudo -n tail -n 100 /var/log/lightdm/lightdm.log; "
            "sudo -n tail -n 100 /var/log/Xorg.0.log; "
            "export DISPLAY=:0 XAUTHORITY=/home/nexus/.Xauthority; "
            + mode_command +
            "printf '\\nNEXUS_SHORTCUT_CONFIG\\n'; "
            "xfconf-query -c xfce4-keyboard-shortcuts -lv; "
            "ls -l /usr/local/bin/nexus-horizon /opt/nexus/horizon.py; "
            "cat /home/nexus/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-keyboard-shortcuts.xml; "
            "xrandr --current; xset q; xprop -root _NET_SUPPORTING_WM_CHECK _NET_CLIENT_LIST; "
            "xwininfo -root -tree; printf '\\nNEXUS_DIAG_%s\\n' END\n"
        )
        client.sendall(command.encode())
        wait_for("NEXUS_DIAG_END", 45)
        print("Initial guest desktop diagnostics collected", flush=True)
        # Wait until keyboard screenshots finish; diagnostic launch must not
        # contaminate evidence of the actual shortcut/direct-key attempts.
        signal = log_path.with_suffix(".keys-done")
        while not signal.exists():
            if time.monotonic() >= deadline:
                raise RuntimeError("Keyboard capture completion absent")
            time.sleep(0.2)
        probe = (
            "printf '\\nNEXUS_HORIZON_PROBE_BEGIN\\n'; "
            "xfconf-query -c xsettings -lv; xfconf-query -c xfce4-desktop -lv; "
            "ls -l /usr/local/libexec/nexus-horizon-appearance; "
            "cat /etc/xdg/autostart/*nexus* /home/nexus/.config/autostart/*nexus* 2>/dev/null; "
            "timeout 20s /usr/local/bin/nexus-horizon >/tmp/nexus-horizon-probe.log 2>&1 & probe_pid=$!; "
            "sleep 10; xwininfo -root -tree; printf 'NEXUS_HORIZON_PROBE_%s\\n' READY; sleep 10; wait \"$probe_pid\"; probe_rc=$?; "
            "printf 'Horizon bounded probe exit=%s (124 means timeout)\\n' \"$probe_rc\"; "
            "cat /tmp/nexus-horizon-probe.log; "
            "printf '\\nNEXUS_HORIZON_PROBE_%s\\n' END\n"
        )
        client.sendall(probe.encode())
        wait_for("NEXUS_HORIZON_PROBE_END", 60)
        print("Bounded Horizon launch diagnostics collected", flush=True)
        # Transfer a fixed repository-owned probe in short canonical-tty lines.
        payload = base64.b64encode(Path(__file__).with_name("windows-guest-probe.py").read_bytes()).decode()
        client.sendall(b": > /tmp/nexus-windows-probe.b64\n")
        for offset in range(0, len(payload), 1000):
            client.sendall(("printf '%s' '" + payload[offset:offset + 1000] + "' >> /tmp/nexus-windows-probe.b64\n").encode())
            time.sleep(0.1)
        client.sendall(b"base64 -d /tmp/nexus-windows-probe.b64 > /tmp/nexus-windows-probe.py; timeout 650s python3 /tmp/nexus-windows-probe.py; printf '\\nNEXUS_WINDOWS_PROBE_EXIT=%s\\n' \"$?\"\n")
        wait_for("NEXUS_WINDOWS_ISO_PASS", 670)
        print("Packaged Windows installer passed in disposable Live guest", flush=True)
        thread.join(timeout=max(0, deadline - time.monotonic()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("socket", type=Path)
    parser.add_argument("log", type=Path)
    parser.add_argument("--full-hd", action="store_true")
    args = parser.parse_args()
    collect(args.socket, args.log, full_hd=args.full_hd)
