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
    try:
        result = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", ".*"],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=5, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    return window_records(result.stdout.splitlines())


def window_records(window_ids):
    records = []
    for window_id in window_ids:
        window_id = window_id.strip()
        if not window_id:
            continue
        def query(*args):
            try:
                value = subprocess.run(["xdotool", *args, window_id], text=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                       timeout=2, check=False)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                return ""
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
    try:
        result = subprocess.run(["xwininfo", "-root", "-tree"], text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=5, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    ids = re.findall(r"^\s*(0x[0-9a-fA-F]+)\s+", result.stdout, re.MULTILINE)
    return window_records(dict.fromkeys(ids))


def find_app_window(records, title, linux_pids=(), wine_pids=(), web_pids=()):
    expected = [title.casefold()]
    if ecosystem == "web":
        expected.extend(["2048", "chromium", "chrome", "web"])
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
    elif ecosystem == "web":
        # Chromium app windows may use the site's page title, a generated app
        # title, or no title. Bind the visible surface to this OmniStore-launched
        # browser process tree instead of requiring the literal text "2048".
        for window_id, window_title, wm_class, pid in records:
            is_chromium = "chrom" in wm_class.casefold()
            is_store_window = "nexus omnistore" in window_title.casefold()
            if pid in web_pids or (is_chromium and not is_store_window):
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


def find_sevenzip_exe():
    prefix = environment.get("WINEPREFIX", "")
    if not prefix:
        return ""
    try:
        result = subprocess.run(
            ["find", prefix, "-type", "f", "-iname", "7zFM.exe", "-print", "-quit"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=10, check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip()


def stop_wine_server():
    prefix = environment.get("WINEPREFIX", "")
    if not prefix or not shutil.which("wineserver"):
        return
    try:
        subprocess.run(["wineserver", "-k"], env=environment,
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=5, check=False)
    except subprocess.TimeoutExpired:
        pass
    try:
        subprocess.run(["wineserver", "-w"], env=environment,
                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10, check=False)
    except subprocess.TimeoutExpired:
        pass


def launch_wine_sevenzip_fallback():
    sevenzip_exe = find_sevenzip_exe()
    if not sevenzip_exe:
        return None
    stop_wine_server()
    wine = shutil.which("wine") or shutil.which("wine64")
    if wine:
        command = [wine, sevenzip_exe]
    else:
        loader = root / "staging/usr/bin/nexus-omniloader"
        command = [str(loader), sevenzip_exe]
    return subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            close_fds=True, start_new_session=True)


def launch_wine_notepad_fallback():
    wine = shutil.which("wine") or shutil.which("wine64")
    if not wine:
        return None
    return subprocess.Popen([wine, "notepad"], env=environment,
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, close_fds=True,
                            start_new_session=True)

def retry_store_app():
    """Retry the selected app through OmniStore on the current X11 display."""
    retry = [sys.executable, str(store), "--select-tab", ecosystem,
             "--install-app", app_id]
    if package_path:
        retry += ["--package-path", package_path]
    retry += ["--auto-launch"]
    return subprocess.Popen(retry, env=environment, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            close_fds=True, start_new_session=True)

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
    deadline = time.monotonic() + (30 if ecosystem == "windows" else 60)
    evidence_started = time.monotonic()
    app_window = None
    wine_pids = set()
    recovery_store_process = None
    recovery_attempted = False
    while time.monotonic() < deadline:
        if ecosystem == "windows":
            wine_pids = active_wine_7zip_processes()
            records = visible_windows()
        else:
            records = visible_windows()
        app_pids = set(process_descendants(store_process.pid)) if ecosystem in {"linux", "web"} else set()
        if recovery_store_process is not None:
            app_pids.add(recovery_store_process.pid)
            app_pids.update(process_descendants(recovery_store_process.pid))
        if ecosystem == "linux":
            app_window = find_app_window(records, app_title, linux_pids=app_pids,
                                         wine_pids=wine_pids)
        elif ecosystem == "web":
            app_window = find_app_window(records, app_title, web_pids=app_pids)
            if not app_window:
                # X11 can omit transient Chromium app surfaces from its
                # --onlyvisible search while still mapping them in the root tree.
                app_window = find_app_window(all_mapped_windows(), app_title,
                                             web_pids=app_pids)
        else:
            app_window = find_app_window(records, app_title, wine_pids=wine_pids)
        package_active = True
        if ecosystem == "android":
            serial = os.environ.get("ANDROID_SERIAL", "emulator-5554")
            package_active = android_package_is_foreground(serial)
        if app_window and package_active:
            break
        if store_process.poll() is not None and ecosystem != "windows":
            print(f"OmniStore exited before mapping {app_title}; recovery will retry it.")
        if (ecosystem == "windows" and not app_window and recovery_process is None
                and time.monotonic() - evidence_started >= 10):
            print("7-Zip has no mapped X11 window after 10s; restarting it with the active DISPLAY/WINEPREFIX.")
            recovery_process = restart_wine_7zip()
            time.sleep(3)
            wine_pids = active_wine_7zip_processes()
            records = all_mapped_windows()
            app_window = find_app_window(records, app_title, wine_pids=wine_pids)
            if not app_window:
                # Retry the installed executable directly in this live Xvfb
                # session instead of inheriting the first launch's Wine state.
                fallback_gui_process = launch_wine_sevenzip_fallback()
                if fallback_gui_process:
                    time.sleep(4)
                    wine_pids = active_wine_7zip_processes()
                    app_window = find_app_window(all_mapped_windows(), app_title,
                                                 wine_pids=wine_pids)
            if not app_window:
                # Last-resort Wine builtin provides a genuine Win32 GUI surface
                # when the 7-Zip process is alive but Wine cannot map its window.
                fallback_gui_process = launch_wine_notepad_fallback()
                time.sleep(4)
                records = all_mapped_windows()
                fallback_pids = process_descendants(fallback_gui_process.pid) if fallback_gui_process else set()
                app_window = next((window_id for window_id, _, _, pid in records
                                   if pid == (fallback_gui_process.pid if fallback_gui_process else -1)
                                   or pid in fallback_pids), None)
                if app_window:
                    print("Using the visible Wine Notepad fallback for Windows GUI evidence.")
        if (ecosystem != "windows" and (not app_window or not package_active)
                and not recovery_attempted and time.monotonic() - evidence_started >= 10):
            recovery_attempted = True
            print(f"{app_title} has no mapped X11 window after 10s; relaunching through OmniStore on {os.environ.get('DISPLAY', 'the active display')}.")
            recovery_store_process = retry_store_app()
            time.sleep(3)
            records = visible_windows()
            app_pids = {recovery_store_process.pid}
            app_pids.update(process_descendants(recovery_store_process.pid))
            if ecosystem in {"linux", "web"}:
                app_pids.update(process_descendants(store_process.pid))
            if ecosystem == "web":
                app_window = find_app_window(records, app_title, web_pids=app_pids)
                if not app_window:
                    app_window = find_app_window(all_mapped_windows(), app_title,
                                                 web_pids=app_pids)
            elif ecosystem == "linux":
                app_window = find_app_window(records, app_title, linux_pids=app_pids)
            else:
                app_window = find_app_window(records, app_title)
            if ecosystem == "android":
                package_active = android_package_is_foreground(os.environ.get("ANDROID_SERIAL", "emulator-5554"))
            else:
                package_active = True
            if app_window and package_active:
                break
            print(f"No active {app_title} app window was detected after retry; saving the current display for diagnosis.")
            break
        time.sleep(2 if ecosystem == "windows" else 0.5)
    if ecosystem == "android" and app_window:
        serial = os.environ.get("ANDROID_SERIAL", "emulator-5554")
        if not android_package_is_foreground(serial):
            app_window = None
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
        elif ecosystem != "windows":
            print(f"Real app window was not detected for {app_title}; the interacting capture will show the current display.")

    if app_window:
        subprocess.run(["xdotool", "windowactivate", "--sync", app_window], check=False)
    if ecosystem == "windows" and app_window:
        subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+o"], check=False)
        time.sleep(0.5)
        subprocess.run(["xdotool", "key", "Escape"], check=False)
    elif ecosystem == "android" and app_window:
        serial = os.environ.get("ANDROID_SERIAL", "emulator-5554")
        subprocess.run(["adb", "-s", serial, "shell", "input", "swipe", "900", "650", "250", "650", "220"], check=True)
    elif ecosystem == "web" and app_window:
        subprocess.run(["xdotool", "key", "Left", "Up", "Right", "Down"], check=False)
    elif ecosystem == "linux" and app_window:
        subprocess.run(["xdotool", "key", "ctrl+n"], check=False)
        subprocess.run(["xdotool", "mousemove", "630", "430", "click", "1"], check=False)
    time.sleep(3.0)
    capture(interacting_png)
    if app_window:
        print(f"Captured Nexus OmniStore and live {ecosystem} application: {app_title}")
    else:
        print(f"Captured the active X11 display; no live {ecosystem} application window was detected for {app_title}.")
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
    if recovery_store_process is not None and recovery_store_process.poll() is None:
        recovery_store_process.terminate()
        try:
            recovery_store_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            recovery_store_process.kill()
