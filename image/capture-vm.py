"""Capture the actual QEMU framebuffer after guest XFCE readiness (QMP).

Captures unchanged framebuffer pixels; controlled keys open menu/run-dialog views.
Does not claim visual quality from readiness markers.
"""
import argparse
import json
from pathlib import Path
import socket
import time


def capture(socket_path, serial_path, output, timeout=240):
    deadline = time.monotonic() + timeout
    markers = ("NEXUS_LIVE_BOOT_READY_V1", "NEXUS_GRAPHICAL_STACK_READY_V1",
               "NEXUS_XFCE_SESSION_READY_V1", "NEXUS_DIAG_END")
    while time.monotonic() < deadline:
        log = serial_path.read_text(errors="replace") if serial_path.exists() else ""
        if all(marker in log for marker in markers) and socket_path.exists():
            break
        time.sleep(1)
    else:
        raise RuntimeError("Guest readiness not observed; no desktop screenshot claimed")
    # Serial diagnostics change display mode. Capture only after that command
    # finishes, then allow the guest compositor to repaint.
    time.sleep(45)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(15)
        client.connect(str(socket_path))
        with client.makefile("rb") as stream:
            greeting = json.loads(stream.readline(1_000_000))
            if "QMP" not in greeting:
                raise RuntimeError("Invalid QMP greeting")
            request_id = 0

            def command(name, arguments):
                nonlocal request_id
                request_id += 1
                client.sendall((json.dumps({"execute": name, "arguments": arguments,
                                           "id": request_id}) + "\n").encode())
                for _ in range(100):
                    response = json.loads(stream.readline(1_000_000))
                    if response.get("id") == request_id:
                        if "error" in response or "return" not in response:
                            raise RuntimeError(f"QMP {name} failed: {response}")
                        return
                raise RuntimeError("QMP reply limit exceeded")

            def screenshot(path):
                command("screendump", {"filename": str(path.resolve()), "format": "png"})

            def key(*codes, settle=10):
                command("send-key", {"keys": [{"type": "qcode", "data": code} for code in codes]})
                time.sleep(settle)

            command("qmp_capabilities", {})
            screenshot(output)
            key("alt", "f1")
            screenshot(output.with_name(output.stem + "-applications.png"))
            key("esc")
            key("alt", "f2")
            screenshot(output.with_name(output.stem + "-run-dialog.png"))
            key("esc")
            key("meta_l", "spc")
            # TCG guests may need additional time to start Python/Tk.
            time.sleep(8)
            screenshot(output.with_name(output.stem + "-horizon.png"))
            # Separate shortcut wiring from launching the packaged executable.
            # Only a fixed command is typed; no user text or shell is evaluated.
            key("esc")
            key("esc")
            key("alt", "f2")
            for code in ("n", "e", "x", "u", "s", "minus", "h", "o", "r", "i", "z", "o", "n"):
                key(code, settle=0.1)
            key("ret", settle=15)
            screenshot(output.with_name(output.stem + "-horizon-direct.png"))
            serial_path.with_suffix(".keys-done").touch()
            ready_deadline = time.monotonic() + 60
            while time.monotonic() < ready_deadline:
                if "NEXUS_HORIZON_PROBE_READY" in serial_path.read_text(errors="replace"):
                    break
                time.sleep(0.2)
            else:
                raise RuntimeError("Bounded launch window inventory absent")
            screenshot(output.with_name(output.stem + "-horizon-probe.png"))
            for marker, suffix in (("NEXUS_WINDOWS_ISO_PREPARED", "-windows-prepared"),
                                   ("NEXUS_WINDOWS_ISO_OPEN", "-windows-open"),
                                   ("NEXUS_WINDOWS_ISO_PASS", None)):
                until = time.monotonic() + 400
                while time.monotonic() < until:
                    if marker in serial_path.read_text(errors="replace"):
                        break
                    time.sleep(0.2)
                else:
                    raise RuntimeError("Live Windows probe absent: " + marker)
                if suffix:
                    screenshot(output.with_name(output.stem + suffix + ".png"))
    probe_deadline = time.monotonic() + 75
    while time.monotonic() < probe_deadline:
        if "NEXUS_HORIZON_PROBE_END" in serial_path.read_text(errors="replace"):
            break
        time.sleep(1)
    else:
        raise RuntimeError("Post-keyboard Horizon launch diagnostics did not complete")
    if not output.is_file() or output.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("No valid PNG framebuffer captured")
    print(f"Actual guest framebuffer captured: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("socket", type=Path)
    parser.add_argument("serial", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    capture(args.socket, args.serial, args.output)
