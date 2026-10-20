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

def windows(title):
    result = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", title],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return [line for line in result.stdout.splitlines() if line.strip()]

environment = os.environ.copy()
environment["NEXUS_RUNTIME_SMOKE"] = str(root / "runtime-smoke.sh")
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
    deadline = time.monotonic() + 240
    app_window = None
    while time.monotonic() < deadline:
        matches = windows(app_title)
        package_active = True
        if ecosystem == "android":
            serial = os.environ.get("ANDROID_SERIAL", "emulator-5554")
            activity = subprocess.run(["adb", "-s", serial, "shell", "dumpsys", "activity", "activities"],
                                      text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            package_active = "org.secuso.privacyfriendly2048" in activity.stdout
        if matches and package_active:
            app_window = matches[0]
            break
        if store_process.poll() is not None:
            raise RuntimeError(f"OmniStore exited before opening {app_title} (status {store_process.returncode})")
        time.sleep(0.25)
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
