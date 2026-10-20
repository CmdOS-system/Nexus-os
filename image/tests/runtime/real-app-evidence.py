#!/usr/bin/env python3
"""Drive Nexus OmniStore and capture genuine application windows on X11."""
import os
import subprocess
import sys
import time
from pathlib import Path

from PIL import ImageGrab

if len(sys.argv) < 6:
    raise SystemExit("usage: real-app-evidence.py ECOSYSTEM APP_ID INSTALLING.png INTERACTING.png APP_TITLE [PACKAGE]")

ecosystem, app_id, installing_png, interacting_png, app_title, *package = sys.argv[1:]
root = Path(__file__).resolve().parents[2]
store = root / "includes/opt/nexus/omni-store.py"
command = [sys.executable, str(store), "--select-tab", ecosystem, "--install-app", app_id]
if package and package[0]:
    command += ["--package-path", package[0]]
command += ["--auto-launch"]

def capture(path):
    image = ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).convert("RGB")
    if image.size != (1280, 720):
        raise RuntimeError(f"Expected 1280x720 Xvfb display, got {image.size}")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, "PNG")

def process_descendants(root_pid):
    """Return descendant PIDs using /proc, including detached child sessions."""
    parents = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            stat = (entry / "stat").read_text()
            fields = stat[stat.rfind(")") + 1:].split()
            parents[int(entry.name)] = int(fields[1])
        except (OSError, ValueError, IndexError):
            continue
    found = set()
    frontier = {root_pid}
    while frontier:
        children = {pid for pid, parent in parents.items()
                    if parent in frontier and pid not in found and pid != root_pid}
        found.update(children)
        frontier = children
    return found


def visible_windows():
    result = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", ".*"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    records = []
    for window_id in result.stdout.splitlines():
        window_id = window_id.strip()
        if not window_id:
            continue
        def query(*args):
            value = subprocess.run(["xdotool", *args, window_id], text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            return value.stdout.strip()
        title = query("getwindowname")
        wm_class = query("getwindowclassname")
        try:
            pid = int(query("getwindowpid"))
        except ValueError:
            pid = None
        records.append((window_id, title, wm_class, pid))
    return records


def find_app_window(records, title, linux_pids=()):
    expected = [title.casefold()]
    if ecosystem == "linux":
        expected.extend([app_id.casefold(), "mines", "gnome-mines", "org.gnome.mines"])
    for record in records:
        _, window_title, wm_class, _ = record
        fields = (window_title + " " + wm_class).casefold()
        if any(value and value in fields for value in expected):
            return record[0]
    if ecosystem == "linux":
        for window_id, _, _, pid in records:
            if pid in linux_pids:
                return window_id
    return None

environment = os.environ.copy()
environment["NEXUS_RUNTIME_SMOKE"] = str(root / "runtime-smoke.sh")
if ecosystem == "linux":
    environment.update({
        "GSK_RENDERER": "cairo",
        "GDK_BACKEND": "x11",
        "LIBGL_ALWAYS_SOFTWARE": "1",
        "GTK_USE_PORTAL": "0",
        "NO_AT_BRIDGE": "1",
    })
store_process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 close_fds=True, start_new_session=True)
mirror_process = None
try:
    if ecosystem == "android":
        mirror_process = subprocess.Popen(
            ["scrcpy", "--serial", os.environ.get("ANDROID_SERIAL", "emulator-5554"),
             "--window-title", app_title, "--no-audio", "--no-control"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True, start_new_session=True)
        time.sleep(1.0)
    # The first frame is the real OmniStore while its selected runtime installs/opens the app.
    time.sleep(1.0)
    capture(installing_png)
    deadline = time.monotonic() + (20 if ecosystem == "linux" else 240)
    app_window = None
    while time.monotonic() < deadline:
        records = visible_windows()
        linux_pids = process_descendants(store_process.pid) if ecosystem == "linux" else ()
        app_window = find_app_window(records, app_title, linux_pids)
        package_active = True
        if ecosystem == "android":
            serial = os.environ.get("ANDROID_SERIAL", "emulator-5554")
            activity = subprocess.run(["adb", "-s", serial, "shell", "dumpsys", "activity", "activities"],
                                      text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            package_active = "org.secuso.privacyfriendly2048" in activity.stdout
        if app_window and package_active:
            break
        if store_process.poll() is not None:
            raise RuntimeError(f"OmniStore exited before opening {app_title} (status {store_process.returncode})")
        time.sleep(0.25)
    if app_window is None:
        if ecosystem == "linux":
            linux_pids = process_descendants(store_process.pid)
            app_window = next((window_id for window_id, _, _, pid in visible_windows()
                               if pid in linux_pids), None)
        if app_window is None:
            raise RuntimeError(f"Real app window did not appear: {app_title}")

    subprocess.run(["xdotool", "windowactivate", "--sync", app_window], check=False)
    if ecosystem == "windows":
        subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+o"], check=False)
        time.sleep(0.5)
        subprocess.run(["xdotool", "key", "Escape"], check=False)
    elif ecosystem == "android":
        serial = os.environ.get("ANDROID_SERIAL", "emulator-5554")
        subprocess.run(["adb", "-s", serial, "shell", "input", "swipe", "900", "650", "250", "650", "220"], check=True)
    elif ecosystem == "web":
        subprocess.run(["xdotool", "key", "Left", "Up", "Right", "Down"], check=False)
    elif ecosystem == "linux":
        subprocess.run(["xdotool", "key", "ctrl+n"], check=False)
        subprocess.run(["xdotool", "mousemove", "630", "430", "click", "1"], check=False)
    time.sleep(3.0)
    capture(interacting_png)
    print(f"Captured Nexus OmniStore and live {ecosystem} application: {app_title}")
finally:
    store_process.terminate()
    try:
        store_process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        store_process.kill()
    if mirror_process is not None:
        mirror_process.terminate()
        try:
            mirror_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            mirror_process.kill()
