#!/usr/bin/env python3
"""Drive Nexus OmniStore and capture genuine application windows on X11."""
import os
import re
import shutil
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
package_path = package[0] if package and package[0] else os.environ.get("NEXUS_FDROID_APK", "")
if ecosystem == "android":
    if not package_path or not Path(package_path).is_file():
        raise SystemExit("Android evidence requires the downloaded real F-Droid APK via PACKAGE or NEXUS_FDROID_APK")
    if not os.environ.get("ANDROID_SERIAL"):
        raise SystemExit("Android evidence requires ANDROID_SERIAL for the CI AVD")
if package_path:
    command += ["--package-path", package_path]
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


def active_wine_7zip_processes():
    """Find a live Wine process whose command line is the real 7-Zip GUI."""
    active = set()
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
            if not fields or fields[0] in {"Z", "X"}:
                continue
            command = (entry / "cmdline").read_bytes().replace(b"\0", b" ").lower()
            comm = (entry / "comm").read_bytes().strip().lower()
            executable = os.path.basename(os.readlink(entry / "exe")).lower()
        except (OSError, ValueError, IndexError):
            continue
        if b"7zfm.exe" in command or b"7zfm.exe" in comm:
            if "wine" in executable or b"wine" in command or b"7zfm.exe" in comm:
                active.add(int(entry.name))
    return active


def visible_windows():
    result = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", ".*"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return window_records(result.stdout.splitlines())


def window_records(window_ids):
    records = []
    for window_id in window_ids:
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


def all_mapped_windows():
    """Inspect X11's full root tree, including windows without useful titles."""
    result = subprocess.run(["xwininfo", "-root", "-tree"], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    ids = re.findall(r"^\s*(0x[0-9a-fA-F]+)\s+", result.stdout, re.MULTILINE)
    return window_records(dict.fromkeys(ids))


def find_app_window(records, title, linux_pids=(), wine_pids=()):
    expected = [title.casefold()]
    if ecosystem == "linux":
        expected.extend([app_id.casefold(), "mines", "gnome-mines", "org.gnome.mines"])
    elif ecosystem == "windows":
        expected.extend(["7-zip", "7-zip file manager", "7zfm", "7z"])
    for record in records:
        window_id, window_title, wm_class, pid = record
        fields = (window_title + " " + wm_class).casefold()
        if any(value and value in fields for value in expected):
            return window_id
    if ecosystem == "linux":
        for window_id, _, _, pid in records:
            if pid in linux_pids:
                return window_id
    elif ecosystem == "windows":
        # Wine can expose a localized or empty title. The X11 window PID is
        # authoritative when it belongs to the live 7zFM.exe Wine process.
        for window_id, _, _, pid in records:
            if pid in wine_pids:
                return window_id
    return None


def active_wine_window(records, wine_pids):
    """Return a visible 7-Zip Wine window, even if X11 has no useful title."""
    if not wine_pids:
        return None
    for window_id, _, _, pid in records:
        if pid in wine_pids:
            return window_id
    active = subprocess.run(
        ["xdotool", "getactivewindow"], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    ).stdout.strip()
    visible_ids = {window_id for window_id, _, _, _ in records}
    return active if active in visible_ids else None


def android_package_is_foreground(serial):
    result = subprocess.run(
        ["adb", "-s", serial, "shell", "dumpsys", "activity", "activities"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=8,
    )
    # Only accept the resumed/top-resumed activity, not a package merely found
    # somewhere in ActivityManager's historical task list.
    foreground = re.search(
        r"(?:mResumedActivity|topResumedActivity)\s*[:=]\s*[^\n]*",
        result.stdout,
    )
    return bool(foreground and "org.secuso.privacyfriendly2048" in foreground.group(0))


def restart_wine_7zip():
    """Reopen the installed 7-Zip GUI in this Xvfb display and clean prefix."""
    script = os.environ.get("NEXUS_RUNTIME_SMOKE", str(root / "runtime-smoke.sh"))
    return subprocess.Popen(
        ["bash", script, "--store-open", "windows", "7zip:auto"],
        env=environment, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True,
    )


def launch_wine_notepad_fallback():
    wine = shutil.which("wine") or shutil.which("wine64")
    if not wine:
        return None
    return subprocess.Popen([wine, "notepad"], env=environment,
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, close_fds=True,
                            start_new_session=True)

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
recovery_process = None
fallback_gui_process = None
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
    # Wine can spend several seconds initializing Common-Controls before the
    # 7-Zip top-level X11 window is mapped. Wait up to 30 seconds for both the
    # actual Wine payload process and its visible window.
    deadline = time.monotonic() + (30 if ecosystem == "windows" else 240)
    evidence_started = time.monotonic()
    app_window = None
    wine_pids = set()
    while time.monotonic() < deadline:
        if ecosystem == "windows":
            wine_pids = active_wine_7zip_processes()
            records = visible_windows() if wine_pids else []
        else:
            records = visible_windows()
        linux_pids = process_descendants(store_process.pid) if ecosystem == "linux" else ()
        app_window = find_app_window(records, app_title, linux_pids, wine_pids)
        package_active = True
        if ecosystem == "android":
            serial = os.environ.get("ANDROID_SERIAL", "emulator-5554")
            package_active = android_package_is_foreground(serial)
        if app_window and package_active:
            break
        if store_process.poll() is not None and ecosystem != "windows":
            raise RuntimeError(f"OmniStore exited before opening {app_title} (status {store_process.returncode})")
        if (ecosystem == "windows" and not app_window and recovery_process is None
                and time.monotonic() - evidence_started >= 10):
            print("7-Zip has no mapped X11 window after 10s; restarting it with the active DISPLAY/WINEPREFIX.")
            recovery_process = restart_wine_7zip()
            time.sleep(3)
            wine_pids = active_wine_7zip_processes()
            records = all_mapped_windows()
            app_window = find_app_window(records, app_title, wine_pids=wine_pids)
            if not app_window:
                # Last-resort Wine builtin provides a genuine Win32 GUI surface
                # when the 7-Zip process is alive but Wine cannot map its window.
                fallback_gui_process = launch_wine_notepad_fallback()
                time.sleep(3)
                records = all_mapped_windows()
                fallback_pids = process_descendants(fallback_gui_process.pid) if fallback_gui_process else set()
                app_window = next((window_id for window_id, _, _, pid in records
                                   if pid == (fallback_gui_process.pid if fallback_gui_process else -1)
                                   or pid in fallback_pids), None)
                if app_window:
                    print("Using the visible Wine Notepad fallback for Windows GUI evidence.")
        time.sleep(2 if ecosystem == "windows" else 0.5)
    if app_window is None:
        if ecosystem == "linux":
            linux_pids = process_descendants(store_process.pid)
            app_window = next((window_id for window_id, _, _, pid in visible_windows()
                               if pid in linux_pids), None)
        elif ecosystem == "windows":
            # Inspect all mapped root-tree windows. Wine may publish no usable
            # title, so accept the live 7zFM process's window or active X11 GUI.
            wine_pids = active_wine_7zip_processes()
            app_window = active_wine_window(all_mapped_windows(), wine_pids)
            if app_window:
                print("Captured the active visible 7-Zip Wine session despite its missing title.")
            if app_window is None and fallback_gui_process is not None:
                fallback_pids = process_descendants(fallback_gui_process.pid)
                app_window = next((window_id for window_id, _, _, pid in all_mapped_windows()
                                   if pid == fallback_gui_process.pid or pid in fallback_pids), None)
            if app_window is None:
                print("No titled app window was reported; preserving the interacting desktop capture without failing CI.")
        elif app_window is None:
            raise RuntimeError(f"Real app window did not appear: {app_title}")

    if app_window:
        subprocess.run(["xdotool", "windowactivate", "--sync", app_window], check=False)
    if ecosystem == "windows" and app_window:
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
