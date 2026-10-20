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

command = [sys.executable, str(store), "--select-tab", ecosystem, "--install-app", app_id]
if package_path:
    command += ["--package-path", package_path]
command += ["--auto-launch"]
environment = os.environ.copy()
environment["NEXUS_RUNTIME_SMOKE"] = str(root / "runtime-smoke.sh")
if ecosystem == "web":
    environment["NEXUS_CHROMIUM_PROFILE"] = "/tmp/chromium-profile"
if ecosystem == "linux":
    environment.update(GSK_RENDERER="cairo", GDK_BACKEND="x11", LIBGL_ALWAYS_SOFTWARE="1",
                       GTK_USE_PORTAL="0", NO_AT_BRIDGE="1")


def top_level_windows():
    """wmctrl lists only managed top-level windows, unlike xdotool's tree search."""
    result = subprocess.run(["wmctrl", "-l", "-G"], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    rows = []
    for line in result.stdout.splitlines():
        fields = line.split(None, 7)
        if len(fields) < 8:
            continue
        try:
            wm_class = subprocess.run(["xprop", "-id", fields[0], "WM_CLASS"], text=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                      check=False).stdout
            class_match = re.search(r'=\s*"([^"]+)"\s*,\s*"([^"]+)"', wm_class)
            class_name = " ".join(class_match.groups()) if class_match else ""
            rows.append({"id": fields[0], "x": int(fields[2]), "y": int(fields[3]),
                         "width": int(fields[4]), "height": int(fields[5]),
                         "class": class_name, "title": fields[7]})
        except ValueError:
            continue
    return rows


def is_store(window):
    return "nexus omnistore" in (window["title"] + " " + window["class"]).casefold()


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


def wait_for_store(timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        window = next((item for item in top_level_windows() if is_store(item)), None)
        if window and window["width"] > 300 and window["height"] > 200:
            return window
        if store_process.poll() is not None:
            raise RuntimeError(f"Nexus OmniStore exited before its window appeared (status {store_process.returncode})")
        time.sleep(0.2)
    raise RuntimeError("Nexus OmniStore top-level window was not mapped")


def wait_for_install_state(timeout=12):
    marker = "cargando" if ecosystem == "web" else "instalando"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        window = next((item for item in top_level_windows() if is_store(item)), None)
        if window and marker in window["title"].casefold():
            return
        time.sleep(0.1)
    raise RuntimeError(f"OmniStore never displayed its real {marker} state for {app_title}")


def android_is_foreground():
    serial = os.environ["ANDROID_SERIAL"]
    result = subprocess.run(["adb", "-s", serial, "shell", "dumpsys", "activity", "activities"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            check=False, timeout=8)
    resumed = re.search(r"(?:mResumedActivity|topResumedActivity)\s*[:=]\s*[^\n]*", result.stdout)
    return bool(resumed and "org.secuso.privacyfriendly2048" in resumed.group(0))


def place_windows(store_window, app_window):
    # Keep both genuine top-level windows visible in the 1280x720 Xvfb frame.
    for window, x, width in ((store_window, 0, 630), (app_window, 640, 630)):
        subprocess.run(["xdotool", "windowmove", window["id"], str(x), "24"], check=False)
        subprocess.run(["xdotool", "windowsize", window["id"], str(width), "670"], check=False)
    subprocess.run(["wmctrl", "-ia", app_window["id"]], check=False)
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
            raise RuntimeError(f"Cannot capture {ecosystem}: OmniStore and the real app must both be top-level windows")
    image = ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).convert("RGB")
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
    subprocess.run(["wmctrl", "-ia", window["id"]], check=False)
    if ecosystem == "web":
        for key in ("Right", "Down", "Left", "Up", "Right", "Down"):
            subprocess.run(["xdotool", "key", "--clearmodifiers", key], check=False)
            time.sleep(0.35)
    elif ecosystem == "android":
        serial = os.environ["ANDROID_SERIAL"]
        for _ in range(3):
            subprocess.run(["adb", "-s", serial, "shell", "input", "swipe", "850", "620", "250", "620", "220"],
                           check=True, timeout=8)
            time.sleep(0.4)
    elif ecosystem == "linux":
        subprocess.run(["xdotool", "mousemove", "950", "430", "click", "1"], check=False)
        subprocess.run(["xdotool", "key", "ctrl+n"], check=False)
    elif ecosystem == "windows":
        subprocess.run(["xdotool", "mousemove", "900", "430", "click", "1"], check=False)
        subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+o"], check=False)
        time.sleep(0.4)
        subprocess.run(["xdotool", "key", "Escape"], check=False)


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


store_process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 close_fds=True, start_new_session=True)
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
    capture(interacting_png, require_two=ecosystem in {"windows", "web", "linux"})
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
    store_process.terminate()
    try:
        store_process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        store_process.kill()
