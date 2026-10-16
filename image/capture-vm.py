"""Capture the actual QEMU framebuffer after guest XFCE readiness (QMP).

Does not inject keys, alter the screenshot, or claim visual quality from markers.
"""
import argparse
import json
from pathlib import Path
import socket
import time


def capture(socket_path, serial_path, output, timeout=240):
    deadline = time.monotonic() + timeout
    markers = ("NEXUS_LIVE_BOOT_READY_V1", "NEXUS_GRAPHICAL_STACK_READY_V1",
               "NEXUS_XFCE_SESSION_READY_V1")
    while time.monotonic() < deadline:
        log = serial_path.read_text(errors="replace") if serial_path.exists() else ""
        if all(marker in log for marker in markers) and socket_path.exists():
            break
        time.sleep(1)
    else:
        raise RuntimeError("Guest readiness not observed; no desktop screenshot claimed")
    time.sleep(5)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(15)
        client.connect(str(socket_path))
        with client.makefile("rb") as stream:
            greeting = json.loads(stream.readline(1_000_000))
            if "QMP" not in greeting:
                raise RuntimeError("Invalid QMP greeting")
            for request_id, command, arguments in (
                (1, "qmp_capabilities", {}),
                (2, "screendump", {"filename": str(output.resolve()), "format": "png"}),
            ):
                client.sendall((json.dumps({"execute": command, "arguments": arguments,
                                           "id": request_id}) + "\n").encode())
                for _ in range(100):
                    response = json.loads(stream.readline(1_000_000))
                    if response.get("id") == request_id:
                        if "error" in response or "return" not in response:
                            raise RuntimeError(f"QMP {command} failed: {response}")
                        break
                else:
                    raise RuntimeError("QMP reply limit exceeded")
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
