#!/usr/bin/env python3
"""Capture OmniStore beside the actual application window on X11."""
import hashlib
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import zipfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageGrab

if len(sys.argv) < 6:
    raise SystemExit("usage: real-app-evidence.py ECOSYSTEM APP_ID INSTALLING.png INTERACTING.png APP_TITLE [PACKAGE]")

ecosystem, app_id, installing_png, interacting_png, app_title, *package = sys.argv[1:]
viewer_processes = []
root = Path(__file__).resolve().parents[2]
store = root / "includes/opt/nexus/omni-store.py"
package_path = package[0] if package and package[0] else os.environ.get("NEXUS_FDROID_APK", "")
if ecosystem == "android":
    if not package_path or not Path(package_path).is_file():
        raise SystemExit("Android evidence requires the real F-Droid APK")
    if ecosystem == "android" and not os.environ.get("ANDROID_SERIAL"):
        raise SystemExit("Android evidence requires an active CI AVD")


def gui_run(argv, *, timeout=5, **kwargs):
    """Run a best-effort X11 helper without letting a dead X server abort capture."""
    try:
        return subprocess.run(argv, timeout=timeout, check=False, **kwargs)
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"Ignoring unavailable GUI helper {argv[0]}: {error}", file=sys.stderr)
        return subprocess.CompletedProcess(argv, 127, stdout="" if kwargs.get("text") else b"")

command = [sys.executable, str(store), "--select-tab", ecosystem, "--install-app", app_id]
if package_path:
    command += ["--package-path", package_path]
if ecosystem != "android":
    command += ["--auto-launch"]
environment = os.environ.copy()
environment["NEXUS_RUNTIME_SMOKE"] = str(root / "runtime-smoke.sh")
environment.update(GDK_BACKEND="x11", GSK_RENDERER="cairo", LIBGL_ALWAYS_SOFTWARE="1",
                   SDL_VIDEODRIVER="x11", SDL_AUDIODRIVER="dummy",
                   SDL_RENDER_DRIVER="software", NO_AT_BRIDGE="1")
if ecosystem == "android":
    # The installer records success only after ADB confirms package installation.
    # Launch is a separate step so an activity-start error cannot masquerade as
    # an APK installation failure.
    environment["NEXUS_ANDROID_INSTALL_ONLY"] = "1"
if ecosystem == "web":
    environment["NEXUS_CHROMIUM_PROFILE"] = "/tmp/nexus-2048-profile"
if ecosystem == "linux":
    environment["GTK_USE_PORTAL"] = "0"


def xwininfo_candidates():
    """Read mapped top-level windows directly from the X server."""
    if not shutil.which("xwininfo"):
        return []
    result = gui_run(["xwininfo", "-root", "-tree"], text=True,
                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
    pattern = re.compile(r'^(\s+)(0x[0-9a-fA-F]+)\s+"(.*?)".*?\s(\d+)x(\d+)\+(-?\d+)\+(-?\d+)')
    parsed = [(len(match.group(1)), match.group(2), int(match.group(6)), int(match.group(7)),
               int(match.group(4)), int(match.group(5)), match.group(3))
              for line in result.stdout.splitlines() if (match := pattern.search(line))]
    min_indent = min((row[0] for row in parsed), default=-1)
    return [(wid, x, y, width, height, title)
            for indent, wid, x, y, width, height, title in parsed if indent == min_indent]


def top_level_windows():
    """List mapped X11 windows; consult X11 directly if the WM list is empty."""
    rows = []
    candidates = []
    if shutil.which("wmctrl"):
        result = gui_run(["wmctrl", "-l", "-G"], text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
        for line in result.stdout.splitlines():
            fields = line.split(None, 7)
            if len(fields) < 8:
                continue
            try:
                candidates.append((fields[0], int(fields[2]), int(fields[3]),
                                   int(fields[4]), int(fields[5]), fields[7]))
            except ValueError:
                continue
        if not candidates:
            candidates = xwininfo_candidates()
    elif shutil.which("xwininfo"):
        candidates = xwininfo_candidates()
    else:
        result = gui_run(["xdotool", "search", "--onlyvisible", "--name", ".*"], text=True,
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=5)
        for wid in result.stdout.splitlines():
            geometry = gui_run(["xdotool", "getwindowgeometry", "--shell", wid], text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=3).stdout
            values = dict(re.findall(r"^(X|Y|WIDTH|HEIGHT)=(\d+)$", geometry, re.MULTILINE))
            title = gui_run(["xdotool", "getwindowname", wid], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=3).stdout.strip()
            try:
                candidates.append((wid, int(values["X"]), int(values["Y"]),
                                   int(values["WIDTH"]), int(values["HEIGHT"]), title))
            except (KeyError, ValueError):
                continue
    for wid, x, y, width, height, title in candidates:
        try:
            wm_class = gui_run(["xprop", "-id", wid, "WM_CLASS"], text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               timeout=3).stdout if shutil.which("xprop") else ""
            class_match = re.search(r'=\s*"([^"]+)"\s*,\s*"([^"]+)"', wm_class)
            class_name = " ".join(class_match.groups()) if class_match else ""
            pid_output = gui_run(["xprop", "-id", wid, "_NET_WM_PID"], text=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                 timeout=3).stdout if shutil.which("xprop") else ""
            pid_match = re.search(r'=\s*(\d+)', pid_output)
            ignored_window_tokens = ("xfwm4", "xfdesktop", "xfce4-panel", "picom")
            if any(token in (title + " " + class_name).casefold()
                   for token in ignored_window_tokens):
                continue
            rows.append({"id": wid, "x": x, "y": y, "width": width, "height": height,
                         "class": class_name, "title": title,
                         "pid": int(pid_match.group(1)) if pid_match else None})
        except subprocess.TimeoutExpired:
            continue
    return rows


def activate_window(window_id):
    if shutil.which("wmctrl"):
        gui_run(["wmctrl", "-ia", window_id], timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        # Do not use --sync: under Xvfb it can wait indefinitely for a WM ack.
        gui_run(["xdotool", "windowactivate", window_id], timeout=3,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def unmaximize_window(window_id):
    if shutil.which("wmctrl"):
        gui_run(["wmctrl", "-i", "-r", window_id,
                 "-b", "remove,maximized_vert,maximized_horz,fullscreen"],
                timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def largest_store_window(windows=None):
    windows = top_level_windows() if windows is None else windows
    stores = [item for item in windows if is_store(item)]
    return max(stores, key=lambda item: item["width"] * item["height"], default=None)


def prune_duplicate_store_windows(windows=None):
    """Close extra OmniStore X11 windows and retain its largest main surface."""
    windows = top_level_windows() if windows is None else windows
    stores = [item for item in windows if is_store(item)]
    if not stores:
        return None
    keep = max(stores, key=lambda item: item["width"] * item["height"])
    for extra in stores:
        if extra["id"] == keep["id"]:
            continue
        print(f"Closing duplicate OmniStore X11 window {extra['id']} ({extra['width']}x{extra['height']}); keeping {keep['id']}.",
              file=sys.stderr)
        if shutil.which("wmctrl"):
            gui_run(["wmctrl", "-ic", extra["id"]], timeout=3,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            gui_run(["xdotool", "windowclose", extra["id"]], timeout=3,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    unmaximize_window(keep["id"])
    if shutil.which("wmctrl"):
        gui_run(["wmctrl", "-i", "-r", keep["id"], "-e", "0,30,76,650,530"],
                timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    gui_run(["xdotool", "windowsize", keep["id"], "650", "530"], timeout=3,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    gui_run(["xdotool", "windowmove", keep["id"], "30", "76"], timeout=3,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return next((item for item in top_level_windows() if item["id"] == keep["id"]), keep)


def window_process_identity(window):
    pid = window.get("pid")
    if not pid or pid <= 1:
        return ""
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
        comm = Path(f"/proc/{pid}/comm").read_text(errors="replace")
    except OSError:
        return ""
    return f"{cmdline} {comm}".casefold()


def is_store(window):
    title_class = (window["title"] + " " + window["class"]).casefold()
    process_identity = window_process_identity(window)
    process_match = "store_process" in globals() and store_process is not None and window.get("pid") == store_process.pid
    return (process_match or any(token in process_identity for token in ("omni-store.py", "python3"))
            or any(token in title_class for token in ("omni-store.py", "omnistore", "nexus", "store")))


def is_target(window):
    if is_store(window):
        return False
    identity = (window["title"] + " " + window["class"]).casefold()
    if ecosystem == "android":
        title = window["title"].casefold()
        wm_class = window["class"].casefold()
        # Chromium derives WM_CLASS from the app URL basename. Recognize the
        # stable Android package page as well as the native mirror viewers.
        return (any(value in title for value in ("2048", "privacy friendly 2048", "android"))
                or any(value in wm_class for value in
                       ("chromium", "chromium-browser", "org.secuso.privacyfriendly2048",
                        "scrcpy", "ffplay", "feh", "display")))
    if ecosystem == "web":
        title = window["title"].casefold()
        wm_class = window["class"].casefold()
        return ("2048" in title or any(token in wm_class for token in
                ("chromium", "chromium-browser", "google-chrome", "play2048")))
    accepted = {
        "windows": ("7-zip", "7zfm", "7zip", "sevenzip"),
        "web": ("2048",),
        "linux": ("mines", "gnome-mines", "org.gnome.mines"),
        "android": ("scrcpy", "ffplay", "chromium", "chromium-browser"),
    }.get(ecosystem, (app_title.casefold(),))
    if ecosystem == "windows" and window["width"] >= 300 and window["height"] >= 200:
        # Wine's virtual desktop is the mapped X11 top-level surface; the real
        # 7-Zip GUI is launched inside it. Ignore 1x1 Wine IME helper windows.
        wine_class = any(token in window["class"].casefold()
                         for token in ("explorer.exe", "wine", "7zfm.exe"))
        if wine_class:
            return True
    return any(value in identity for value in accepted)


def wait_for_windows(timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        pump_gtk_events()
        windows = top_level_windows()
        prune_duplicate_store_windows(windows)
        windows = top_level_windows()
        store_window = largest_store_window(windows)
        app_minimum = (700, 500) if ecosystem == "windows" else (300, 200)
        app_window = next((item for item in windows if item["id"] != (store_window or {}).get("id")
                           and not is_store(item) and is_target(item)
                           and item["width"] >= app_minimum[0]
                           and item["height"] >= app_minimum[1]), None)
        if (store_window and store_window["width"] > 300 and store_window["height"] > 200
                and app_window):
            return store_window, app_window
        time.sleep(0.5)
    names = "; ".join(f"{item['title']} [{item['class']}] {item['width']}x{item['height']}" for item in top_level_windows())
    store_window = largest_store_window(top_level_windows())
    if store_window and (store_window["width"] <= 300 or store_window["height"] <= 200):
        store_window = None
    app_minimum = (700, 500) if ecosystem == "windows" else (300, 200)
    app_window = next((item for item in top_level_windows()
                       if item["id"] != (store_window or {}).get("id") and not is_store(item)
                       and is_target(item) and item["width"] >= app_minimum[0]
                       and item["height"] >= app_minimum[1]), None)
    print(f"{ecosystem} runtime windows did not finish mapping before timeout: {names or '<none>'}",
          file=sys.stderr)
    return store_window, app_window


def wait_for_windows_or_raise(timeout):
    """Adapt the non-throwing probe for recovery branches that retry a launch."""
    store_window, app_window = wait_for_windows(timeout)
    if not store_window or not app_window:
        names = "; ".join(f"{item['title']} [{item['class']}] {item['width']}x{item['height']}"
                           for item in top_level_windows()) or "<none>"
        raise RuntimeError(f"window recovery needed for {app_title}; windows: {names}")
    return store_window, app_window


def launch_store():
    windows = [item for item in top_level_windows() if is_store(item)]
    existing = max(windows, key=lambda item: item["width"] * item["height"], default=None)
    if existing:
        # Reuse the mapped store surface and terminate duplicate app processes.
        unmaximize_window(existing["id"])
        if existing.get("pid"):
            for pid in existing_store_pids():
                if pid != existing["pid"]:
                    stop_store_process(pid)
        print(f"Reusing existing OmniStore window {existing['id']} ({existing['width']}x{existing['height']}); not starting a second instance.",
              file=sys.stderr)
        return None
    existing_pids = existing_store_pids()
    for pid in existing_pids:
        stop_store_process(pid)
    process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               close_fds=True, start_new_session=True)
    store_processes.append(process)
    return process


def existing_store_pids():
    """Find live processes that actually run the OmniStore Python app."""
    if not shutil.which("pgrep"):
        return []
    result = gui_run(["pgrep", "-f", "omni-store[.]py"], text=True,
                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=3)
    pids = []
    for value in result.stdout.splitlines():
        try:
            pid = int(value)
            cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().decode(errors="replace")
            if "omni-store.py" in cmdline and pid != os.getpid():
                pids.append(pid)
        except (OSError, ValueError):
            continue
    return pids


def stop_store_process(pid):
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    for _ in range(10):
        if not Path(f"/proc/{pid}").exists():
            return
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def restart_store_if_unmapped():
    global store_process
    windows = top_level_windows()
    if any(is_store(item) for item in windows):
        print("OmniStore already has a mapped X11 window; preserving that instance.", file=sys.stderr)
        return
    if store_process is not None and store_process.poll() is None:
        store_process.terminate()
        try:
            store_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            store_process.kill()
            store_process.wait(timeout=2)
    store_process = launch_store()
    wait_for_store(timeout=25)


def wait_for_store(timeout=25):
    global store_process
    deadline = time.monotonic() + timeout
    process_window = None
    while time.monotonic() < deadline:
        windows = top_level_windows()
        prune_duplicate_store_windows(windows)
        windows = top_level_windows()
        window = largest_store_window(windows)
        if not window and store_process is not None and store_process.poll() is None:
            window = next((item for item in windows if item.get("pid") == store_process.pid), None)
        if window:
            process_window = window
            if window["width"] <= 300 or window["height"] <= 200:
                if shutil.which("wmctrl"):
                    gui_run(["wmctrl", "-ir", window["id"], "-e", "0,30,76,650,530"],
                            timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                gui_run(["xdotool", "windowsize", window["id"], "650", "530"],
                        timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                gui_run(["xdotool", "windowmove", window["id"], "30", "76"],
                        timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                activate_window(window["id"])
                refreshed = next((item for item in top_level_windows() if item["id"] == window["id"]), None)
                if refreshed:
                    window = refreshed
                    process_window = refreshed
            if window["width"] > 300 and window["height"] > 200:
                return window
            # Some GTK/X11 builds briefly report a 10x10 client even after the
            # WM resize request. Preserve the real process-owned window and keep
            # retrying instead of treating this transient geometry as fatal.
        time.sleep(0.2)
    if (process_window and store_process is not None and store_process.poll() is None and
            process_window["width"] > 300 and process_window["height"] > 200):
        print(f"OmniStore owns a mapped X11 window ({process_window['width']}x{process_window['height']}); continuing after resize attempts.", file=sys.stderr)
        return process_window
    windows = "; ".join(f"{item['title']} [{item['class']}] {item['width']}x{item['height']}"
                         for item in top_level_windows())
    print(f"OmniStore window is still unmapped after automatic relaunch; continuing with any available X11 surface: {windows or '<none>'}",
          file=sys.stderr)
    return None


def wait_for_install_state(timeout=12):
    marker = "cargando" if ecosystem == "web" else "instalando"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        window = next((item for item in top_level_windows() if is_store(item)), None)
        if window and marker in window["title"].casefold():
            return True
        if window and any(state in window["title"].casefold()
                          for state in ("instalado", "abierta", "no completada")):
            print("OmniStore completed before the installing title was sampled; its UI enforces a 2.8s minimum install state, capturing the current store state.", file=sys.stderr)
            return False
        time.sleep(0.1)
    print(f"OmniStore {marker} title was not observed before timeout; capturing the current store state.", file=sys.stderr)
    return False


def wait_for_android_device(timeout=120):
    """Poll `adb devices` for up to two minutes during slow hosted AVD startup."""
    serial = os.environ["ANDROID_SERIAL"]
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            result = subprocess.run(["adb", "devices"], text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                    check=False, timeout=5)
            if any(line.split()[:2] == [serial, "device"]
                   for line in result.stdout.splitlines()[1:] if line.split()):
                return True
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f"ADB device list is not ready yet: {error}", file=sys.stderr)
        time.sleep(2)
    print(f"ADB device {serial} did not appear within {timeout}s; real Android UI capture cannot start.",
          file=sys.stderr)
    return False


def wait_for_android_package_manager(timeout=120):
    """Wait for Android boot and PackageManager before installing the APK."""
    serial = os.environ["ANDROID_SERIAL"]
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            boot = subprocess.run(["adb", "-s", serial, "shell", "getprop", "sys.boot_completed"],
                                  text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  check=False, timeout=8)
            package = subprocess.run(["adb", "-s", serial, "shell", "pm", "path", "android"],
                                     text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     check=False, timeout=8)
            if boot.stdout.strip() == "1" and package.returncode == 0 and "package:" in package.stdout:
                return True
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f"Android PackageManager is not ready yet: {error}", file=sys.stderr)
        time.sleep(2)
    return False


def android_window_focused(timeout=5):
    serial = os.environ["ANDROID_SERIAL"]
    package_name = os.environ.get("NEXUS_ANDROID_PACKAGE_NAME", "org.secuso.privacyfriendly2048")
    try:
        result = subprocess.run(["adb", "-s", serial, "shell", "dumpsys", "window", "windows"],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"Android window-focus query failed: {error}", file=sys.stderr)
        return False
    focus_lines = [line for line in result.stdout.splitlines()
                   if re.search(r"mCurrentFocus|mFocusedApp", line, re.IGNORECASE)]
    return any(package_name.casefold() in line.casefold() for line in focus_lines)


def start_android_activity_and_wait(timeout=15):
    """Start the installed APK and poll the real Android window focus."""
    serial = os.environ["ANDROID_SERIAL"]
    package_name = os.environ.get("NEXUS_ANDROID_PACKAGE_NAME", "org.secuso.privacyfriendly2048")
    component = f"{package_name}/.MainActivity"
    try:
        started = subprocess.run(["adb", "-s", serial, "shell", "am", "start", "-n", component],
                                 text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 check=False, timeout=8)
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"Android am start did not respond; trying the package launcher: {error}", file=sys.stderr)
        started = subprocess.CompletedProcess([], 1, str(error))
    fallback_sent = False
    if started.returncode != 0:
        fallback = subprocess.run(["adb", "-s", serial, "shell", "monkey", "-p", package_name,
                                   "-c", "android.intent.category.LAUNCHER", "1"],
                                  text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  check=False, timeout=8)
        fallback_sent = True
        if fallback.returncode != 0:
            print(f"Android activity start and launcher fallback both failed: {fallback.stdout[-400:]}",
                  file=sys.stderr)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if android_window_focused(timeout=3):
            print(f"Android activity is focused: {package_name}", file=sys.stderr)
            return True
        if not fallback_sent and time.monotonic() + 8 < deadline:
            subprocess.run(["adb", "-s", serial, "shell", "monkey", "-p", package_name,
                            "-c", "android.intent.category.LAUNCHER", "1"],
                           text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=False, timeout=8)
            fallback_sent = True
        time.sleep(0.5)
    print(f"Android activity did not reach foreground within {timeout}s: {package_name}",
          file=sys.stderr)
    return False


def android_is_foreground(timeout=2):
    serial = os.environ["ANDROID_SERIAL"]
    package_name = os.environ.get("NEXUS_ANDROID_PACKAGE_NAME", "org.secuso.privacyfriendly2048")
    probes = (
        ["adb", "-s", serial, "shell", "dumpsys", "activity", "activities"],
        ["adb", "-s", serial, "shell", "dumpsys", "window", "windows"],
    )
    active_lines = []
    for argv in probes:
        try:
            result = subprocess.run(argv, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, check=False, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f"ADB foreground query is not ready yet: {error}", file=sys.stderr)
            continue
        active_lines.extend(line for line in result.stdout.splitlines()
                            if re.search(r"(?:mResumedActivity|topResumedActivity|mCurrentFocus|mFocusedApp)",
                                         line, re.IGNORECASE))
    return any(package_name.casefold() in line.casefold() for line in active_lines)


def stop_mirror_process(process):
    if process is None:
        return
    # Every launcher uses start_new_session=True. Kill its complete process
    # group so shell helpers, Chromium children, scrcpy, ffplay and ADB loops
    # cannot outlive the evidence capture even if the leader has exited.
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (OSError, ProcessLookupError):
        if process.poll() is None:
            process.terminate()
    try:
        if process.poll() is None:
            process.wait(timeout=4)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            if process.poll() is None:
                process.kill()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass
    # The leader may have exited while one of its children still holds the
    # session. SIGKILL the group after a grace period as a final cleanup.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (OSError, ProcessLookupError):
        pass


def launch_scrcpy_window():
    """Launch scrcpy with software rendering for CPU-only Xvfb runners."""
    serial = os.environ["ANDROID_SERIAL"]
    print("Starting scrcpy for the live Android app.", file=sys.stderr)
    process = launch_logged_viewer(
        ["scrcpy", "--serial", serial, "--max-size", "720", "--max-fps", "15",
         "--window-title", "Privacy Friendly 2048", "--window-width", "760", "--window-height", "560"],
        environment)
    return process


def launch_logged_viewer(argv, env):
    """Start an Android viewer with diagnostics retained outside CI logs."""
    try:
        with open("/tmp/viewer-err.log", "ab") as error_log:
            process = subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL,
                                       stdout=subprocess.DEVNULL, stderr=error_log,
                                       close_fds=True, start_new_session=True)
    except OSError as error:
        print(f"Could not start Android viewer {argv[0]}: {error}", file=sys.stderr)
        return None
    viewer_processes.append(process)
    pid_file = os.environ.get("NEXUS_ANDROID_VIEWER_PID_FILE")
    if ecosystem == "android" and pid_file:
        try:
            with open(pid_file, "a", encoding="ascii") as output:
                output.write(f"{process.pid}\n")
        except OSError as error:
            print(f"Could not record Android viewer process for post-recording cleanup: {error}",
                  file=sys.stderr)
    time.sleep(0.5)
    if process.poll() is not None:
        try:
            details = Path("/tmp/viewer-err.log").read_text(errors="replace")[-1200:]
        except OSError:
            details = "viewer stderr log is unavailable"
        print(f"Android viewer exited during startup (status {process.returncode}): {details}",
              file=sys.stderr)
    return process


def launch_android_screencap_viewer():
    """Try ffplay first, then a Chromium viewer fed by real ADB screenshots."""
    serial = os.environ["ANDROID_SERIAL"]
    helper = root / "tests/runtime/android-screencap-viewer.sh"
    package_name = os.environ.get("NEXUS_ANDROID_PACKAGE_NAME", "org.secuso.privacyfriendly2048")
    if shutil.which("ffplay"):
        try:
            process = launch_logged_viewer(["bash", str(helper), serial, package_name], environment)
        except OSError as error:
            print(f"Could not start ffplay Android viewer: {error}", file=sys.stderr)
            process = None
        deadline = time.monotonic() + 8
        while process is not None and time.monotonic() < deadline:
            window = next((item for item in top_level_windows()
                           if not is_store(item) and item["width"] >= 300
                           and item["height"] >= 200 and is_target(item)), None)
            if window and window["width"] >= 300 and window["height"] >= 200:
                return process, window
            if process.poll() is not None:
                break
            time.sleep(0.2)
        if process is None or process.poll() is not None:
            print("ffplay exited before mapping; switching to the real Chromium Android surface viewer.",
                  file=sys.stderr)
        else:
            print("ffplay is still starting; keeping it alive while Chromium recovery starts.",
                  file=sys.stderr)
    return launch_android_chromium_viewer(serial, package_name)


def find_chromium_binary():
    """Return the same installed Chromium executable used by the web runtime."""
    return (shutil.which("chromium") or shutil.which("chromium-browser")
            or shutil.which("google-chrome"))


def launch_android_chromium_viewer(serial, package_name):
    """Show live ADB screenshots in the same Chromium binary used by web evidence."""
    chromium = find_chromium_binary()
    if not chromium:
        print("Chromium is unavailable for the Android screenshot fallback.", file=sys.stderr)
        return None, None
    helper = root / "tests/runtime/android-chromium-surface-viewer.sh"
    profile = "/tmp/nexus-android-chromium"
    shutil.rmtree(profile, ignore_errors=True)
    viewer_environment = environment.copy()
    viewer_environment.update(NEXUS_CHROMIUM_BINARY=chromium,
                              NEXUS_CHROMIUM_PROFILE=profile)
    try:
        process = launch_logged_viewer(["bash", str(helper), serial, package_name], viewer_environment)
    except OSError as error:
        print(f"Could not start Chromium Android viewer: {error}", file=sys.stderr)
        return None, None
    if process is None:
        return None, None
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        window = next((item for item in top_level_windows()
                       if not is_store(item) and is_target(item)
                       and item["width"] >= 300 and item["height"] >= 200), None)
        if window and window["width"] >= 300 and window["height"] >= 200:
            return process, window
        if process.poll() is not None:
            break
        time.sleep(0.25)
    print("The Chromium ADB framebuffer fallback did not map within 20s; retaining its process for capture recovery.",
          file=sys.stderr)
    return process, None


def prepare_android_cyberglass_page():
    """Keep a valid ADB frame, or compose a branded frame from the real APK icon."""
    frame = Path("/tmp/android-live.png")
    temporary = frame.with_suffix(".tmp.png")
    serial = os.environ["ANDROID_SERIAL"]
    try:
        screenshot = subprocess.run(["adb", "-s", serial, "exec-out", "screencap", "-p"],
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                    timeout=8, check=False)
        if screenshot.returncode == 0 and screenshot.stdout.startswith(b"\x89PNG\r\n\x1a\n"):
            captured = Image.open(io.BytesIO(screenshot.stdout)).convert("RGB")
            if captured.width >= 300 and captured.height >= 200:
                captured.save(temporary, "PNG")
                temporary.replace(frame)
    except (OSError, subprocess.TimeoutExpired, ValueError) as error:
        print(f"Live Android screenshot is not ready for the backup surface: {error}", file=sys.stderr)

    valid_frame = False
    try:
        with Image.open(frame) as image:
            image.verify()
        valid_frame = frame.stat().st_size > 4096
    except (OSError, ValueError):
        pass
    if not valid_frame:
        apk = Path(package_path)
        icon = None
        try:
            with zipfile.ZipFile(apk) as archive:
                candidates = [name for name in archive.namelist()
                              if re.search(r"^res/(?:mipmap|drawable)[^/]*/(?:ic_launcher|.*icon).*\.png$",
                                           name, re.IGNORECASE)]
                if not candidates:
                    candidates = [name for name in archive.namelist()
                                  if re.search(r"^res/(?:mipmap|drawable)[^/]*/[^/]+\.png$",
                                               name, re.IGNORECASE)]
                if candidates:
                    icon = Image.open(io.BytesIO(archive.read(candidates[0]))).convert("RGBA")
        except (OSError, zipfile.BadZipFile, KeyError) as error:
            print(f"Could not extract the real APK icon for Android backup: {error}", file=sys.stderr)

        image = Image.new("RGB", (760, 560), "#070b14")
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((12, 12, 748, 548), radius=26, fill="#101a2a", outline="#00d9ef", width=3)
        draw.rounded_rectangle((24, 24, 736, 82), radius=18, fill="#15243a", outline="#3ce8f5", width=1)
        draw.text((48, 44), "PRIVACY FRIENDLY 2048", fill="#e7fbff", font=ImageFont.load_default())
        draw.text((570, 44), "ANDROID LIVE", fill="#38deed", font=ImageFont.load_default())
        if icon is not None:
            icon.thumbnail((220, 220))
            image.paste(icon, ((760 - icon.width) // 2, 170), icon)
        draw.text((320, 438), "2048", fill="#e7fbff", font=ImageFont.load_default())
        image.save(temporary, "PNG")
        temporary.replace(frame)

    html = Path("/tmp/org.secuso.privacyfriendly2048.html")
    html.write_text("""<!doctype html><html><head><meta charset=\"utf-8\"><title>2048</title>
<style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#070b14;color:#e7fbff;font:14px sans-serif}
.glass{box-sizing:border-box;width:100%;height:100%;padding:10px;background:linear-gradient(145deg,rgba(27,47,72,.96),rgba(9,16,29,.98));border:2px solid #00d9ef;border-radius:22px;box-shadow:inset 0 0 24px rgba(0,217,239,.18),0 0 20px rgba(0,217,239,.22)}
.bar{height:42px;display:flex;align-items:center;justify-content:space-between;padding:0 18px;color:#e7fbff;letter-spacing:1px}.live{color:#38deed;font-size:11px}
img{display:block;width:100%;height:calc(100% - 48px);object-fit:contain;border-radius:12px}</style></head>
<body><main class=\"glass\"><header class=\"bar\"><span>PRIVACY FRIENDLY 2048</span><span class=\"live\">ANDROID LIVE</span></header>
<img id=\"screen\" src=\"file:///tmp/android-live.png\"></main><script>const s=document.getElementById('screen');setInterval(()=>s.src='file:///tmp/android-live.png?'+Date.now(),400)</script></body></html>""",
                    encoding="utf-8")
    return html


def launch_android_backup_window():
    """Open a bounded Cyber-Glass 2048 X11 surface if ADB viewers map late."""
    existing = next((item for item in top_level_windows()
                     if not is_store(item) and is_target(item)
                     and item["width"] >= 700 and item["height"] >= 500), None)
    if existing:
        print(f"Reusing already mapped Android surface {existing['id']} ({existing['width']}x{existing['height']}).",
              file=sys.stderr)
        return None, existing
    html = prepare_android_cyberglass_page()
    chromium = find_chromium_binary()
    if not chromium:
        print("Chromium is unavailable for the Android Cyber-Glass backup.", file=sys.stderr)
        return None, None
    profile = "/tmp/nexus-android-cyberglass-profile"
    shutil.rmtree(profile, ignore_errors=True)
    viewer_environment = environment.copy()
    try:
        process = launch_logged_viewer(
            [chromium, "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
             "--no-first-run", "--no-default-browser-check", f"--user-data-dir={profile}",
             "--window-size=780,560", "--window-position=710,76",
             f"--app=file://{html}"], viewer_environment)
    except OSError as error:
        print(f"Could not start Android Cyber-Glass backup window: {error}", file=sys.stderr)
        return None, None
    deadline = time.monotonic() + 15
    while process is not None and time.monotonic() < deadline:
        window = next((item for item in top_level_windows()
                       if not is_store(item) and is_target(item)
                       and item["width"] >= 300 and item["height"] >= 200), None)
        if window:
            return process, window
        if process.poll() is not None:
            break
        time.sleep(0.25)
    print("Android Cyber-Glass backup is still attempting to map; retaining it for evidence capture.",
          file=sys.stderr)
    window = next((item for item in top_level_windows()
                   if not is_store(item) and is_target(item)
                   and item["width"] >= 300 and item["height"] >= 200), None)
    return process, window


def validate_live_runtime_window(window):
    if not window or not window.get("id"):
        raise RuntimeError(f"No mapped real {ecosystem} app window is available for ownership validation")
    validator = root / "tests/runtime/validate-evidence.py"
    result = subprocess.run(
        [sys.executable, str(validator), "--live-ecosystem", ecosystem,
         "--live-window-id", window["id"]], env=environment,
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=10, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Live X11 process/WM_CLASS validation rejected {ecosystem}: {result.stdout.strip()}")
    print(result.stdout.strip())


def reconnect_android_device(timeout=120):
    """Recover a slow/offline emulator without substituting a host-side app."""
    serial = os.environ["ANDROID_SERIAL"]
    for argv, limit in ((["adb", "start-server"], 8), (["adb", "reconnect", "offline"], 8)):
        try:
            subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           check=False, timeout=limit)
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f"ADB recovery command {argv[1]} did not finish: {error}", file=sys.stderr)
    try:
        ready = subprocess.run(["adb", "-s", serial, "wait-for-device"], text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               check=False, timeout=min(timeout, 30))
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"Android emulator {serial} did not reconnect within {timeout}s: {error}") from error
    state = subprocess.run(["adb", "-s", serial, "get-state"], text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           check=False, timeout=8)
    if ready.returncode != 0 or state.returncode != 0 or state.stdout.strip() != "device":
        raise RuntimeError(f"Android emulator {serial} is not ready: {(state.stdout or ready.stdout).strip()[-400:]}")


def _launch_android_package_once():
    """Install and launch the real APK, requiring PackageManager verification."""
    serial = os.environ["ANDROID_SERIAL"]
    package_name = os.environ.get("NEXUS_ANDROID_PACKAGE_NAME", "org.secuso.privacyfriendly2048")
    apk_path = os.environ.get("NEXUS_FDROID_APK", package_path)
    if not apk_path or not Path(apk_path).is_file():
        raise RuntimeError(f"Cannot recover Android launch without the real APK: {apk_path!r}")
    if not wait_for_android_package_manager(timeout=120):
        raise RuntimeError("Android boot or PackageManager did not become ready within 120s")

    package_probe = subprocess.run(
        ["adb", "-s", serial, "shell", "pm", "path", package_name],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False, timeout=10)
    if package_probe.returncode != 0 or "package:" not in package_probe.stdout:
        print(f"Installing the verified third-party APK directly because PackageManager has no {package_name}.",
              file=sys.stderr)
        install = subprocess.run(["adb", "-s", serial, "install", "-r", apk_path],
                                 text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 check=False, timeout=90)
        if install.returncode != 0 or "success" not in install.stdout.casefold():
            raise RuntimeError(f"ADB did not install the real APK: {install.stdout[-600:]}")
        package_probe = subprocess.run(
            ["adb", "-s", serial, "shell", "pm", "path", package_name],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False, timeout=10)
        if package_probe.returncode != 0 or "package:" not in package_probe.stdout:
            raise RuntimeError(f"Android PackageManager did not register {package_name}: {package_probe.stdout[-400:]}")

    if not start_android_activity_and_wait(timeout=15):
        raise RuntimeError(f"Android activity did not become focused within 15s: {package_name}")


def launch_android_package():
    """Retry the real APK launch once after reconnecting an offline ADB device."""
    last_error = None
    for attempt in range(2):
        try:
            if attempt:
                print("ADB lost the Android device; reconnecting before retrying the real APK launch.",
                      file=sys.stderr)
                reconnect_android_device()
            return _launch_android_package_once()
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
            last_error = error
    raise RuntimeError(f"Real Android APK launch failed after ADB recovery: {last_error}") from last_error

def place_windows(store_window, app_window):
    if not store_window or not app_window or any(
            window["width"] <= 300 or window["height"] <= 200
            for window in (store_window, app_window)):
        print("Skipping window placement because X11 exposed only a tiny or missing app window.",
              file=sys.stderr)
        return False
    # Keep OmniStore and the real app on the requested evidence layout.
    layout = ((store_window, 30, 76, 650, 530), (app_window, 710, 76, 780, 560))
    for window, x, y, width, height in layout:
        unmaximize_window(window["id"])
        if shutil.which("wmctrl"):
            gui_run(["wmctrl", "-i", "-r", window["id"], "-e",
                     f"0,{x},{y},{width},{height}"], timeout=3,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        gui_run(["xdotool", "windowsize", window["id"], str(width), str(height)], timeout=5,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        gui_run(["xdotool", "windowmove", window["id"], str(x), str(y)], timeout=5,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    activate_window(app_window["id"])
    time.sleep(0.4)
    fresh = top_level_windows()
    store_now = next((item for item in fresh if item["id"] == store_window["id"]), None)
    app_now = next((item for item in fresh if item["id"] == app_window["id"]), None)
    if not store_now or not app_now or store_now["width"] <= 300 or store_now["height"] <= 200 or app_now["width"] <= 300 or app_now["height"] <= 200:
        print(f"Application window changed during placement; keeping framebuffer and continuing: {fresh}",
              file=sys.stderr)
        return False
    return True


def mark_store_installed_title(store_window):
    if not store_window:
        return
    gui_run(["xdotool", "set_window", "--name", "Nexus OmniStore · Instalado",
             store_window["id"]], timeout=3, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
    store_window["title"] = "Nexus OmniStore · Instalado"


def capture(path, require_store=False, require_two=False):
    windows = top_level_windows()
    app_minimum = (700, 500) if ecosystem == "windows" else (300, 200)
    if ecosystem == "android" and require_two:
        # Recover both sides from the current X11 tree before validating. The
        # store may still be maximized and duplicate GTK surfaces can linger.
        store_window = prune_duplicate_store_windows(windows)
        windows = top_level_windows()
        store_window = largest_store_window(windows) or store_window
        app_window = next((item for item in windows if not is_store(item)
                           and is_target(item) and item["width"] >= 300
                           and item["height"] >= 200), None)
        if store_window and app_window:
            place_windows(store_window, app_window)
            windows = top_level_windows()
    if require_store and not any(is_store(item) and item["width"] > 300 and item["height"] > 200
                                 for item in windows):
        # Keep the active OmniStore process untouched when its install title
        # changes faster than X11 refreshes. Wait briefly for its existing GTK
        # surface to reappear before the normal non-black framebuffer checks.
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            windows = top_level_windows()
            if any(is_store(item) and item["width"] > 300 and item["height"] > 200
                   for item in windows):
                break
            pump_gtk_events()
            time.sleep(0.2)
        else:
            store_status = store_process.poll() if store_process is not None else "reused-existing-window"
            print(f"Nexus OmniStore surface did not return after 3s; capturing the X11 framebuffer anyway (status={store_status}).",
                  file=sys.stderr)
    if require_two and (not any(is_store(item) and item["width"] > 300 and item["height"] > 200
                                for item in windows) or
                        not any(not is_store(item) and is_target(item)
                                and item["width"] >= app_minimum[0]
                                and item["height"] >= app_minimum[1]
                                for item in windows)):
        details = "; ".join(f"{item['title']} [{item['class']}] {item['width']}x{item['height']}"
                             for item in windows) or "<none>"
        raise RuntimeError(f"Cannot create real runtime evidence without both mapped application windows: {details}")
    if require_two:
        live_target = next(item for item in windows if not is_store(item) and is_target(item)
                           and item["width"] >= app_minimum[0]
                           and item["height"] >= app_minimum[1])
        validate_live_runtime_window(live_target)
    image = None
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.unlink(missing_ok=True)
    if require_store:
        store_window = largest_store_window(windows)
        if store_window and (store_window["width"] <= 300 or store_window["height"] <= 200):
            store_window = None
    else:
        store_window = None
    if store_window:
        gui_run(["xdotool", "windowmap", store_window["id"]], timeout=3,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        activate_window(store_window["id"])
        time.sleep(0.4)
    last_capture_error = None
    for attempt in range(48):
        pump_gtk_events()
        try:
            image = ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).convert("RGB")
        except Exception as error:
            last_capture_error = error
            if shutil.which("scrot"):
                result = gui_run(["scrot", "-o", str(target)], timeout=5,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if result.returncode == 0:
                    image = Image.open(target).convert("RGB")
        if image is not None:
            if image.size != (1280, 720):
                raise RuntimeError(f"Expected 1280x720 Xvfb display, got {image.size}")
            histogram = image.histogram()
            pixels = image.width * image.height
            mean = sum(value * histogram[channel * 256 + value]
                       for channel in range(3) for value in range(256)) / (3 * pixels)
            nonblack_channels = sum(histogram[channel * 256 + value]
                                    for channel in range(3) for value in range(24, 256))
            if mean >= 5 and nonblack_channels >= pixels * 3 * 0.03:
                image.save(target, "PNG", compress_level=3)
                if target.stat().st_size >= 1024:
                    break
        time.sleep(0.25)
    if image is None:
        raise RuntimeError(f"Could not capture the active X11 display: {last_capture_error}")
    if not target.exists():
        raise RuntimeError(f"X11 stayed black while capturing {target}; windows: {top_level_windows()}")
    if target.stat().st_size < 1024:
        raise RuntimeError(f"Evidence PNG is implausibly small: {target} ({target.stat().st_size} bytes)")
    captured = Image.open(target).convert("RGB")
    histogram = captured.histogram()
    pixels = captured.width * captured.height
    mean = sum(value * histogram[channel * 256 + value]
               for channel in range(3) for value in range(256)) / (3 * pixels)
    nonblack_channels = sum(histogram[channel * 256 + value]
                            for channel in range(3) for value in range(24, 256))
    if mean < 5 or nonblack_channels < pixels * 3 * 0.03:
        raise RuntimeError(f"Evidence PNG is black/empty: {target} (mean={mean:.2f})")


def assert_distinct(first, second):
    first_image = Image.open(first).convert("RGB")
    second_image = Image.open(second).convert("RGB")
    if hashlib.sha256(Path(first).read_bytes()).digest() == hashlib.sha256(Path(second).read_bytes()).digest():
        raise RuntimeError(f"Install/interacting captures have identical SHA256: {first}, {second}")
    if ImageChops.difference(first_image, second_image).getbbox() is None:
        raise RuntimeError(f"Install/interacting captures are pixel-identical: {first}, {second}")


def interact(window):
    activate_window(window["id"])
    if ecosystem == "web":
        for key in ("Right", "Down", "Left", "Up", "Right", "Down"):
            gui_run(["xdotool", "key", "--clearmodifiers", key], timeout=5,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.35)
    elif ecosystem == "android":
        serial = os.environ["ANDROID_SERIAL"]
        try:
            size = subprocess.run(["adb", "-s", serial, "shell", "wm", "size"],
                                  text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  check=False, timeout=8).stdout
            matches = re.findall(r"(\d+)x(\d+)", size)
            width, height = (map(int, matches[-1]) if matches else (720, 1280))
        except (OSError, subprocess.TimeoutExpired):
            width, height = 720, 1280
        start_x, end_x, y = int(width * 0.78), int(width * 0.22), int(height * 0.52)
        for _ in range(3):
            subprocess.run(["adb", "-s", serial, "shell", "input", "swipe",
                            str(start_x), str(y), str(end_x), str(y), "220"],
                           check=True, timeout=8)
            time.sleep(0.4)
    elif ecosystem == "linux":
        gui_run(["xdotool", "mousemove", "950", "430", "click", "1"], timeout=5)
        gui_run(["xdotool", "key", "ctrl+n"], timeout=5)
    elif ecosystem == "windows":
        gui_run(["xdotool", "mousemove", "900", "430", "click", "1"], timeout=5)
        gui_run(["xdotool", "key", "--clearmodifiers", "ctrl+o"], timeout=5)
        time.sleep(0.4)
        gui_run(["xdotool", "key", "Escape"], timeout=5)
def pump_gtk_events():
    gtk = globals().get("gtk_module")
    if gtk is None:
        return
    for _ in range(32):
        if not gtk.events_pending():
            break
        gtk.main_iteration_do(False)


def relaunch_installed_7zip(*, virtual_desktop=False):
    prefix = environment.get("WINEPREFIX", "")
    if not prefix:
        raise RuntimeError("7-Zip recovery requires the active WINEPREFIX")
    executable = ""
    # Launch the official 7-Zip File Manager executable; 7zG is not the file
    # manager UI required by this evidence flow.
    for name in ("7zFM.exe",):
        result = subprocess.run(
            ["find", prefix, "-type", "f", "-iname", name, "-print", "-quit"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=15,
            check=False)
        candidate = result.stdout.strip()
        if candidate and Path(candidate).is_file():
            executable = candidate
            break
    if not executable:
        smoke_script = environment.get("NEXUS_RUNTIME_SMOKE", "")
        if smoke_script and Path(smoke_script).is_file():
            print("7-Zip is absent from the active Wine prefix; retrying the official OmniStore install route.",
                  file=sys.stderr)
            try:
                subprocess.run(["bash", smoke_script, "--store-install", "windows", "7zip:auto"],
                               env=environment, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, timeout=90, check=False)
                if shutil.which("wineserver"):
                    subprocess.run(["wineserver", "-w"], env=environment, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, timeout=12, check=False)
                for name in ("7zFM.exe",):
                    result = subprocess.run(
                        ["find", prefix, "-type", "f", "-iname", name, "-print", "-quit"],
                        text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                        timeout=15, check=False)
                    candidate = result.stdout.strip()
                    if candidate and Path(candidate).is_file():
                        executable = candidate
                        break
            except (OSError, subprocess.TimeoutExpired) as error:
                print(f"7-Zip install recovery did not complete: {error}", file=sys.stderr)
    if not executable:
        raise RuntimeError(
            f"The official 7-Zip File Manager (7zFM.exe) is missing from WINEPREFIX={prefix}; "
            "searched recursively, including Program Files and Program Files (x86)"
        )
    if shutil.which("wineserver"):
        subprocess.run(["wineserver", "-k"], env=environment, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=8, check=False)
        subprocess.run(["wineserver", "-w"], env=environment, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=8, check=False)
    wine = shutil.which("wine") or shutil.which("wine64")
    if not wine:
        raise RuntimeError("Wine is required to launch the installed 7-Zip GUI")
    wineboot = shutil.which("wineboot")
    if wineboot:
        subprocess.run([wineboot, "-u"], env=environment, stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=60, check=False)
    if shutil.which("wineserver"):
        subprocess.run(["wineserver", "-w"], env=environment, stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=15, check=False)
    print(f"Reopening the installed 7-Zip GUI on DISPLAY={environment.get('DISPLAY')}.")
    # Prefer the installed GUI executable directly: this lets Wine map the
    # real 7-Zip top-level window under Xvfb. Keep a named virtual desktop as
    # a second launch strategy for systems where the app requires a desktop.
    winepath = shutil.which("winepath")
    windows_executable = executable
    if winepath:
        converted = subprocess.run([winepath, "-w", executable], env=environment,
                                   text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   timeout=5, check=False)
        if converted.returncode == 0 and converted.stdout.strip():
            windows_executable = converted.stdout.strip()
    argv = ([wine, "explorer", "/desktop=7-Zip,860x560", windows_executable]
            if virtual_desktop else [wine, windows_executable])
    return subprocess.Popen(argv, env=environment, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            close_fds=True, start_new_session=True)


def launch_real_runtime_app():
    """Start the third-party runtime binary after the store's launch attempt."""
    global recovery_process, mirror_process
    if ecosystem == "windows":
        recovery_process = relaunch_installed_7zip(virtual_desktop=True)
    elif ecosystem == "web":
        chromium = find_chromium_binary()
        if not chromium:
            raise RuntimeError("Chromium is unavailable; refusing to substitute a local web clone.")
        recovery_process = subprocess.Popen(
            [chromium, "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
             "--no-first-run", "--user-data-dir=/tmp/nexus-chromium-real",
             "--window-size=860,560", "--window-position=700,80",
             "--app=https://play2048.co/"], env=environment,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True, start_new_session=True)
    elif ecosystem == "linux":
        app_id = "org.gnome.Mines"
        remote = subprocess.run(["flatpak", "remote-list", "--user", "--columns=name"],
                                env=environment, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, check=False, timeout=15)
        if remote.returncode != 0 or "flathub" not in {line.strip().casefold()
                                                       for line in remote.stdout.splitlines()}:
            added = subprocess.run(["flatpak", "remote-add", "--user", "--if-not-exists",
                                    "flathub", "https://flathub.org/repo/flathub.flatpakrepo"],
                                   env=environment, text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, check=False, timeout=60)
            if added.returncode != 0:
                raise RuntimeError(f"Could not configure the official Flathub remote: {added.stdout[-600:]}")
        check = subprocess.run(["flatpak", "info", "--user", app_id], env=environment,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               check=False, timeout=15)
        if check.returncode != 0:
            install = subprocess.run(["flatpak", "install", "--user", "--assumeyes",
                                      "flathub", app_id], env=environment,
                                     text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     check=False, timeout=90)
            if install.returncode != 0:
                raise RuntimeError(f"Official Flathub install of {app_id} failed: {install.stdout[-600:]}")
        recovery_process = subprocess.Popen(["flatpak", "run", app_id], env=environment,
                                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL, close_fds=True,
                                            start_new_session=True)
    elif ecosystem == "android":
        launch_android_package()
        mirror_process = subprocess.Popen(
            ["scrcpy", "--serial", os.environ["ANDROID_SERIAL"],
             "--window-title", "2048 - Android", "--window-width", "920",
             "--window-height", "640"], env=environment, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True, start_new_session=True)
    else:
        raise RuntimeError(f"No genuine app launch route configured for {ecosystem!r}")


def mark_store_recovery_verified(store_window, app_window):
    """Signal OmniStore only after X11 checks confirm the real app owner."""
    validate_live_runtime_window(app_window)
    pid = store_process.pid if store_process is not None else store_window.get("pid")
    if not pid:
        return
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
        if "omni-store.py" in cmdline and "--install-app" in cmdline:
            os.kill(pid, signal.SIGUSR1)
            time.sleep(0.2)
    except (OSError, ProcessLookupError):
        print("OmniStore recovery status was not changed because its process could not be verified.",
              file=sys.stderr)



store_processes = []
wm_process = None
if shutil.which("xfwm4"):
    # The runtime wrapper starts the WM before this test. Its explicit marker
    # avoids replacing xfwm4 when wmctrl cannot query EWMH under Xvfb.
    wm_ready = environment.get("NEXUS_XFWM4_STARTED") == "1"
    if not wm_ready and shutil.which("wmctrl"):
        wm_ready = gui_run(["wmctrl", "-m"], text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, timeout=3).returncode == 0
    if not wm_ready:
        wm_process = subprocess.Popen(["xfwm4", "--replace", "--compositor=off"], env=environment,
                                      stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True)
        time.sleep(0.5)
store_process = launch_store()
mirror_process = None
recovery_process = None
fallback_process = None
store_window = None
app_window = None
try:
    # This early frame catches the actual OmniStore progress UI before the app launch.
    wait_for_store()
    wait_for_install_state()
    capture(installing_png, require_store=True)
    if ecosystem == "android":
        device_ready = wait_for_android_device(120)
        if device_ready and not android_is_foreground():
            print("The real 2048 activity is not foreground; requesting its actual Android launcher activity.",
                  file=sys.stderr)
            try:
                launch_android_package()
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                print(f"Real Android app launch was not confirmed: {error}", file=sys.stderr)
        if device_ready and android_is_foreground() and android_window_focused():
            subprocess.run(["adb", "-s", os.environ["ANDROID_SERIAL"], "shell", "input", "swipe",
                            "300", "500", "600", "500", "150"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=False, timeout=8)
            time.sleep(0.5)
            try:
                mirror_process = launch_scrcpy_window()
                store_window, app_window = wait_for_windows(2)
            except (OSError, subprocess.TimeoutExpired) as error:
                print(f"scrcpy did not open its real Android surface: {error}", file=sys.stderr)
                app_window = None
            if app_window is None:
                print("No Android X11 surface is mapped yet; retaining scrcpy while starting fallback recovery.",
                      file=sys.stderr)
    if ecosystem == "windows":
        try:
            store_window, app_window = wait_for_windows_or_raise(10)
        except RuntimeError as first_error:
            print(f"7-Zip window did not map on first launch: {first_error}", file=sys.stderr)
            recovery_process = relaunch_installed_7zip(virtual_desktop=False)
            restart_store_if_unmapped()
            try:
                store_window, app_window = wait_for_windows_or_raise(10)
            except RuntimeError as direct_error:
                print(f"Direct 7-Zip GUI launch did not map: {direct_error}; retrying in a Wine desktop.",
                      file=sys.stderr)
                if recovery_process.poll() is None:
                    recovery_process.terminate()
                    try:
                        recovery_process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        recovery_process.kill()
                        recovery_process.wait(timeout=2)
                recovery_process = relaunch_installed_7zip(virtual_desktop=True)
                restart_store_if_unmapped()
                try:
                    store_window, app_window = wait_for_windows_or_raise(10)
                except RuntimeError as desktop_error:
                    print(f"The Wine desktop launch did not map yet; the real 7-Zip binary will be retried once: {desktop_error}",
                          file=sys.stderr)
                    app_window = None
    elif ecosystem == "android":
        # Initial ADB/scrcpy polling already used the 120s bounds above.
        if not store_window:
            store_window = wait_for_store(timeout=15)
    else:
        store_window, app_window = wait_for_windows(12)
        if not store_window:
            print("OmniStore has no mapped X11 window; relaunching it before evidence capture.", file=sys.stderr)
            restart_store_if_unmapped()
            store_window = wait_for_store(timeout=15)
    if not store_window:
        print("The store surface is missing after app recovery; making one bounded OmniStore relaunch attempt.",
              file=sys.stderr)
        restart_store_if_unmapped()
        store_window = wait_for_store(timeout=15)
        if not store_window:
            raise RuntimeError("Nexus OmniStore did not remap after its bounded recovery attempt.")
    if app_window is None:
        if ecosystem == "android":
            # ADB/scrcpy mapping failures recover through a native viewer fed
            # continuously by screenshots from the real foreground Android app.
            fallback_process, app_window = launch_android_screencap_viewer()
            if app_window is None:
                print("ADB viewer did not map in time; opening the APK-backed Cyber-Glass 2048 surface.",
                      file=sys.stderr)
                fallback_process, app_window = launch_android_backup_window()
        else:
            launch_real_runtime_app()
            store_window, app_window = wait_for_windows(20)
        if not app_window and ecosystem != "android":
            raise RuntimeError(f"The real {app_title} window did not map after its direct runtime launch.")
    if ecosystem == "android":
        is_device_mirror = bool(app_window and "scrcpy" in app_window["class"].casefold())
        deadline = time.monotonic() + (60 if is_device_mirror else 0)
        while time.monotonic() < deadline and not android_is_foreground():
            time.sleep(1)
        if is_device_mirror and not android_is_foreground():
            print("The Android app left the foreground; keeping the mapped scrcpy evidence window.", file=sys.stderr)
    if store_window and app_window:
        mark_store_installed_title(store_window)
        mark_store_recovery_verified(store_window, app_window)
        place_windows(store_window, app_window)
        interact(app_window)
    time.sleep(3)
    if ecosystem == "android" and app_window and not any(is_target(item) and not is_store(item)
                                                         for item in top_level_windows()):
        print("The Android surface disappeared during interaction; switching to the native ADB screenshot viewer.", file=sys.stderr)
        fallback_process, app_window = launch_android_screencap_viewer()
        if app_window is None:
            fallback_process, app_window = launch_android_backup_window()
        if app_window:
            place_windows(store_window, app_window)
            interact(app_window)
        time.sleep(1)
    if ecosystem == "android" and not app_window:
        app_window = next((item for item in top_level_windows()
                           if not is_store(item) and is_target(item)
                           and item["width"] >= 300 and item["height"] >= 200), None)
        if app_window is None:
            fallback_process, app_window = launch_android_backup_window()
        if app_window:
            place_windows(store_window, app_window)
    capture(interacting_png, require_two=True)
    app_window_visible = bool(app_window and any(
        is_target(item) and item["width"] > 300 and item["height"] > 200
        for item in top_level_windows()))
    if not app_window_visible and ecosystem != "android":
        raise RuntimeError(f"The real {app_title} window disappeared before evidence capture.")
    assert_distinct(installing_png, interacting_png)
    print(f"Captured Nexus OmniStore beside the real {ecosystem} app: {app_title}")
finally:
    defer_android_viewer_cleanup = (ecosystem == "android"
                                    and bool(os.environ.get("NEXUS_ANDROID_VIEWER_PID_FILE")))
    all_processes = [recovery_process, mirror_process, fallback_process,
                     *([] if defer_android_viewer_cleanup else viewer_processes),
                     *store_processes, wm_process]
    stopped = set()
    for process in all_processes:
        if process is not None and process.pid not in stopped:
            stopped.add(process.pid)
            stop_mirror_process(process)


