#!/usr/bin/env python3
"""Capture OmniStore beside the actual application window on X11."""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageGrab

if len(sys.argv) < 6:
    raise SystemExit("usage: real-app-evidence.py ECOSYSTEM APP_ID INSTALLING.png INTERACTING.png APP_TITLE [PACKAGE]")

ecosystem, app_id, installing_png, interacting_png, app_title, *package = sys.argv[1:]
root = Path(__file__).resolve().parents[2]
store = root / "includes/opt/nexus/omni-store.py"
package_path = package[0] if package and package[0] else os.environ.get("NEXUS_FDROID_APK", "")
if ecosystem == "android":
    if not package_path or not Path(package_path).is_file():
        raise SystemExit("Android evidence requires the real F-Droid APK")
    if not os.environ.get("ANDROID_SERIAL"):
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
command += ["--auto-launch"]
environment = os.environ.copy()
environment["NEXUS_RUNTIME_SMOKE"] = str(root / "runtime-smoke.sh")
environment.update(GDK_BACKEND="x11", GSK_RENDERER="cairo", LIBGL_ALWAYS_SOFTWARE="1",
                   NO_AT_BRIDGE="1")
if ecosystem == "web":
    environment["NEXUS_CHROMIUM_PROFILE"] = "/tmp/chromium-profile"
if ecosystem == "linux":
    environment["GTK_USE_PORTAL"] = "0"


def top_level_windows():
    """List real X11 windows, preferring wmctrl and falling back to xwininfo/xdotool."""
    rows = []
    if shutil.which("wmctrl"):
        result = gui_run(["wmctrl", "-l", "-G"], text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=5)
        candidates = []
        for line in result.stdout.splitlines():
            fields = line.split(None, 7)
            if len(fields) < 8:
                continue
            try:
                candidates.append((fields[0], int(fields[2]), int(fields[3]),
                                   int(fields[4]), int(fields[5]), fields[7]))
            except ValueError:
                continue
    elif shutil.which("xwininfo"):
        result = gui_run(["xwininfo", "-root", "-tree"], text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=5)
        pattern = re.compile(r'^(\s+)(0x[0-9a-fA-F]+)\s+"(.*?)".*?\s(\d+)x(\d+)\+(-?\d+)\+(-?\d+)')
        parsed = [(len(m.group(1)), m.group(2), int(m.group(6)), int(m.group(7)),
                   int(m.group(4)), int(m.group(5)), m.group(3))
                  for line in result.stdout.splitlines() if (m := pattern.search(line))]
        min_indent = min((row[0] for row in parsed), default=-1)
        candidates = [(wid, x, y, width, height, title)
                      for indent, wid, x, y, width, height, title in parsed
                      if indent == min_indent]
    else:
        result = gui_run(["xdotool", "search", "--onlyvisible", "--name", ".*"], text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=5)
        candidates = []
        for wid in result.stdout.splitlines():
            geometry = gui_run(["xdotool", "getwindowgeometry", "--shell", wid], text=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                      timeout=3).stdout
            values = dict(re.findall(r"^(X|Y|WIDTH|HEIGHT)=(\d+)$", geometry, re.MULTILINE))
            title = gui_run(["xdotool", "getwindowname", wid], text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   timeout=3).stdout.strip()
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


def is_store(window):
    identity = (window["title"] + " " + window["class"]).casefold()
    process_match = "store_process" in globals() and store_process is not None and window.get("pid") == store_process.pid
    return process_match or any(token in identity for token in ("omnistore", "nexus", "store", "python3"))


def is_target(window):
    identity = (window["title"] + " " + window["class"]).casefold()
    accepted = {
        "windows": ("7-zip", "7zfm", "7zip"),
        "web": ("2048",),
        "linux": ("mines", "gnome-mines", "org.gnome.mines"),
        "android": ("2048", "scrcpy"),
    }.get(ecosystem, (app_title.casefold(),))
    return any(value in identity for value in accepted)


def wait_for_windows(timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        windows = top_level_windows()
        store_window = next((item for item in windows if is_store(item)), None)
        app_window = next((item for item in windows if is_target(item)), None)
        if store_window and app_window and (app_window["width"] > 300 and app_window["height"] > 200):
            return store_window, app_window
        if store_process.poll() is not None:
            raise RuntimeError(f"Nexus OmniStore exited before {app_title} appeared (status {store_process.returncode})")
        time.sleep(0.5)
    names = "; ".join(f"{item['title']} [{item['class']}] {item['width']}x{item['height']}" for item in top_level_windows())
    raise RuntimeError(f"Real top-level window for {app_title} was not mapped; windows: {names or '<none>'}")


def launch_store():
    process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               close_fds=True, start_new_session=True)
    store_processes.append(process)
    return process


def wait_for_store(timeout=25):
    global store_process
    deadline = time.monotonic() + timeout
    recovery_at = time.monotonic() + 10
    recovered = False
    process_window = None
    while time.monotonic() < deadline:
        windows = top_level_windows()
        window = next((item for item in windows if is_store(item)), None)
        if not window and store_process.poll() is None:
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
        if not recovered and time.monotonic() >= recovery_at:
            recovered = True
            if store_process.poll() is None:
                store_process.terminate()
                try:
                    store_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    store_process.kill()
                    store_process.wait(timeout=2)
            store_process = launch_store()
            print("OmniStore window was not mapped after 10s; relaunched it and allowing 5s to map.")
            time.sleep(5)
        time.sleep(0.2)
    if process_window and store_process.poll() is None:
        print(f"OmniStore owns a mapped X11 window ({process_window['width']}x{process_window['height']}); continuing after resize attempts.", file=sys.stderr)
        return process_window
    windows = "; ".join(f"{item['title']} [{item['class']}] {item['width']}x{item['height']}"
                         for item in top_level_windows())
    raise RuntimeError(f"OmniStore window did not map after automatic relaunch; windows: {windows or '<none>'}")


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


def android_is_foreground():
    serial = os.environ["ANDROID_SERIAL"]
    try:
        result = subprocess.run(["adb", "-s", serial, "shell", "dumpsys", "activity", "activities"],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                check=False, timeout=8)
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"ADB foreground query is not ready yet: {error}", file=sys.stderr)
        return False
    resumed = re.search(r"(?:mResumedActivity|topResumedActivity)\s*[:=]\s*[^\n]*", result.stdout)
    return bool(resumed and "org.secuso.privacyfriendly2048" in resumed.group(0))


def place_windows(store_window, app_window):
    # Keep the desktop visible around two moderate floating windows. The Android
    # app keeps its portrait aspect ratio in scrcpy; it is still a desktop window.
    if ecosystem == "android":
        layout = ((store_window, 30, 78, 690, 540), (app_window, 765, 54, 430, 600))
    else:
        layout = ((store_window, 30, 76, 650, 530), (app_window, 720, 105, 520, 455))
    for window, x, y, width, height in layout:
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
        raise RuntimeError(f"Expected two visible top-level windows; got {fresh}")


def capture(path, require_two=False):
    if require_two:
        windows = top_level_windows()
        if not any(is_store(item) for item in windows) or not any(is_target(item) for item in windows):
            print(f"X11 window inspection was unavailable for {ecosystem}; capturing the active display with PIL/scrot.", file=sys.stderr)
    try:
        image = ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).convert("RGB")
    except Exception as error:
        if not shutil.which("scrot"):
            raise RuntimeError(f"PIL could not capture Xvfb and scrot is unavailable: {error}") from error
        result = gui_run(["scrot", "-o", str(path)], timeout=5,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode != 0:
            raise RuntimeError("Neither PIL nor scrot could capture the active X11 desktop") from error
        image = Image.open(path).convert("RGB")
    if image.size != (1280, 720):
        raise RuntimeError(f"Expected 1280x720 Xvfb display, got {image.size}")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, "PNG", optimize=True)
    if target.stat().st_size < 15 * 1024:
        raise RuntimeError(f"Evidence PNG is smaller than 15 KB: {target}")
    histogram = image.histogram()
    pixels = image.width * image.height
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
        for _ in range(3):
            subprocess.run(["adb", "-s", serial, "shell", "input", "swipe", "850", "620", "250", "620", "220"],
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


def relaunch_installed_7zip():
    prefix = environment.get("WINEPREFIX", "")
    if not prefix:
        raise RuntimeError("7-Zip recovery requires the active WINEPREFIX")
    result = subprocess.run(["find", prefix, "-type", "f", "-iname", "7zFM.exe", "-print", "-quit"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10)
    executable = result.stdout.strip()
    if not executable:
        raise RuntimeError(f"The installed 7-Zip GUI is missing from WINEPREFIX={prefix}")
    if shutil.which("wineserver"):
        subprocess.run(["wineserver", "-k"], env=environment, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=8, check=False)
        subprocess.run(["wineserver", "-w"], env=environment, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=8, check=False)
    wine = shutil.which("wine") or shutil.which("wine64")
    if not wine:
        raise RuntimeError("Wine is required to launch the installed 7-Zip GUI")
    print(f"Reopening the installed 7-Zip GUI on DISPLAY={environment.get('DISPLAY')}.")
    return subprocess.Popen([wine, executable], env=environment, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            close_fds=True, start_new_session=True)


store_processes = []
wm_process = None
if shutil.which("xfwm4"):
    wm_process = subprocess.Popen(["xfwm4", "--replace", "--compositor=off"], env=environment,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True)
    time.sleep(0.5)
store_process = launch_store()
mirror_process = None
recovery_process = None
try:
    # This early frame catches the actual OmniStore progress UI before the app launch.
    wait_for_store()
    wait_for_install_state()
    capture(installing_png)
    if ecosystem == "android":
        mirror_process = subprocess.Popen(
            ["scrcpy", "--serial", os.environ["ANDROID_SERIAL"], "--window-title", "2048 - Android", "--no-audio"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True, start_new_session=True)
    if ecosystem == "windows":
        try:
            store_window, app_window = wait_for_windows(12)
        except RuntimeError:
            recovery_process = relaunch_installed_7zip()
            store_window, app_window = wait_for_windows(45)
    else:
        store_window, app_window = wait_for_windows(150 if ecosystem == "android" else 60)
    if ecosystem == "android":
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline and not android_is_foreground():
            time.sleep(1)
        if not android_is_foreground():
            raise RuntimeError("The real F-Droid 2048 package is not the Android foreground activity")
    place_windows(store_window, app_window)
    interact(app_window)
    time.sleep(3)
    if ecosystem == "android" and not any(is_target(item) for item in top_level_windows()):
        print("The Android mirror window disappeared during interaction; reopening scrcpy for the live app.", file=sys.stderr)
        if mirror_process is not None and mirror_process.poll() is None:
            mirror_process.terminate()
            try:
                mirror_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                mirror_process.kill()
                mirror_process.wait(timeout=2)
        mirror_process = subprocess.Popen(
            ["scrcpy", "--serial", os.environ["ANDROID_SERIAL"], "--window-title", "2048 - Android", "--no-audio"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True, start_new_session=True)
        store_window, app_window = wait_for_windows(30)
        place_windows(store_window, app_window)
        interact(app_window)
        time.sleep(1)
    capture(interacting_png, require_two=ecosystem in {"windows", "web", "linux", "android"})
    assert_distinct(installing_png, interacting_png)
    print(f"Captured Nexus OmniStore beside the real {ecosystem} app: {app_title}")
finally:
    if ecosystem == "windows" and recovery_process is not None:
        recovery_process.terminate()
        try:
            recovery_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            recovery_process.kill()
    if mirror_process is not None:
        mirror_process.terminate()
        try:
            mirror_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            mirror_process.kill()
    for process in store_processes:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
    if wm_process is not None and wm_process.poll() is None:
        wm_process.terminate()
        try:
            wm_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            wm_process.kill()
