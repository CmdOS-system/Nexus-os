#!/usr/bin/env python3
"""Capture OmniStore beside the actual application window on X11."""
import hashlib
import json
import os
import re
import shutil
import signal
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
                   NO_AT_BRIDGE="1")
if ecosystem == "android":
    # The installer records success only after ADB confirms package installation.
    # Launch is a separate step so an activity-start error cannot masquerade as
    # an APK installation failure.
    environment["NEXUS_ANDROID_INSTALL_ONLY"] = "1"
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
    if ecosystem == "web" and "chrom" in identity and not is_store(window):
        return True
    accepted = {
        "windows": ("7-zip", "7zfm", "7zip", "sevenzip"),
        "web": ("2048",),
        "linux": ("mines", "gnome-mines", "org.gnome.mines"),
        "android": ("2048", "scrcpy"),
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
        store_window = next((item for item in windows if is_store(item)), None)
        app_window = next((item for item in windows if is_target(item)
                           and item["width"] > 300 and item["height"] > 200), None)
        if (store_window and store_window["width"] > 300 and store_window["height"] > 200
                and app_window):
            return store_window, app_window
        if store_process.poll() is not None and ecosystem not in {"android", "windows"}:
            raise RuntimeError(f"Nexus OmniStore exited before {app_title} appeared (status {store_process.returncode})")
        time.sleep(0.5)
    names = "; ".join(f"{item['title']} [{item['class']}] {item['width']}x{item['height']}" for item in top_level_windows())
    if ecosystem == "android":
        store_window = next((item for item in top_level_windows()
                             if is_store(item) and item["width"] > 300 and item["height"] > 200), None)
        print(f"{ecosystem} application window was not mapped; preserving the available desktop: {names or '<none>'}",
              file=sys.stderr)
        return store_window, None
    raise RuntimeError(f"Real top-level window for {app_title} was not mapped; windows: {names or '<none>'}")


def launch_store():
    process = subprocess.Popen(command, env=environment, stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               close_fds=True, start_new_session=True)
    store_processes.append(process)
    return process


def restart_store_if_unmapped():
    global store_process
    windows = top_level_windows()
    if any(is_store(item) and item["width"] > 300 and item["height"] > 200 for item in windows):
        return
    if store_process.poll() is None:
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
    if (process_window and store_process.poll() is None and
            process_window["width"] > 300 and process_window["height"] > 200):
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
    package_name = os.environ.get("NEXUS_ANDROID_PACKAGE_NAME", "org.secuso.privacyfriendly2048")
    probes = (
        ["adb", "-s", serial, "shell", "dumpsys", "activity", "activities"],
        ["adb", "-s", serial, "shell", "dumpsys", "window", "windows"],
    )
    active_lines = []
    for argv in probes:
        try:
            result = subprocess.run(argv, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL, check=False, timeout=10)
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f"ADB foreground query is not ready yet: {error}", file=sys.stderr)
            continue
        active_lines.extend(line for line in result.stdout.splitlines()
                            if re.search(r"(?:mResumedActivity|topResumedActivity|mCurrentFocus|mFocusedApp)",
                                         line, re.IGNORECASE))
    return any(package_name.casefold() in line.casefold() for line in active_lines)


def stop_mirror_process(process):
    if process is None or process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (OSError, ProcessLookupError):
        process.terminate()
    try:
        process.wait(timeout=4)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            process.kill()
        process.wait(timeout=3)


def launch_android_framebuffer_viewer():
    """Show the live framebuffer streamed from the real ADB device in a desktop window."""
    ffplay = shutil.which("ffplay")
    if not ffplay:
        raise RuntimeError("Android screen mirror fallback requires ffplay from the installed FFmpeg package")
    serial = os.environ["ANDROID_SERIAL"]
    command = (
        f'adb -s "{serial}" exec-out screenrecord --output-format=h264 - | '
        f'"{ffplay}" -hide_banner -loglevel error -an -f h264 -i pipe:0 '
        '-window_title "2048 - Android" -x 430 -y 600'
    )
    print("scrcpy did not map a desktop window; opening a live ADB framebuffer stream in ffplay.",
          file=sys.stderr)
    return subprocess.Popen(["bash", "-o", "pipefail", "-c", command], env=environment,
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True)


def launch_android_package():
    """Install if needed, resolve, and launch the APK's real Android activity."""
    serial = os.environ["ANDROID_SERIAL"]
    package_name = os.environ.get("NEXUS_ANDROID_PACKAGE_NAME", "org.secuso.privacyfriendly2048")
    apk_path = os.environ.get("NEXUS_FDROID_APK", package_path)
    if not apk_path or not Path(apk_path).is_file():
        raise RuntimeError(f"Cannot recover Android launch without the real APK: {apk_path!r}")

    candidates = []
    configured = os.environ.get("NEXUS_ANDROID_LAUNCH_ACTIVITY", "").strip()
    if configured:
        candidates.append(configured if "/" in configured else
                          f"{package_name}/{configured if not configured.startswith('.') else package_name + configured}")

    def resolve_activity():
        try:
            result = subprocess.run(
                ["adb", "-s", serial, "shell", "cmd", "package", "resolve-activity", "--brief",
                 "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER",
                 "-p", package_name],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                check=False, timeout=15)
            for line in reversed(result.stdout.splitlines()):
                component = line.strip()
                if "/" in component and package_name.casefold() in component.casefold():
                    return component
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f"PackageManager activity resolution failed: {error}", file=sys.stderr)
        return ""

    def attempt_launch():
        resolved = resolve_activity()
        launch_candidates = list(dict.fromkeys([*candidates, resolved]))
        failures = []
        for component in launch_candidates:
            if not component:
                continue
            try:
                result = subprocess.run(
                    ["adb", "-s", serial, "shell", "am", "start", "-W", "-n", component],
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    check=False, timeout=30)
            except (OSError, subprocess.TimeoutExpired) as error:
                failures.append(f"{component}: {error}")
                continue
            if result.returncode == 0:
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    if android_is_foreground():
                        return True, failures
                    time.sleep(0.5)
            failures.append(f"{component} (exit {result.returncode}): {result.stdout[-400:]}")

        try:
            result = subprocess.run(
                ["adb", "-s", serial, "shell", "am", "start", "-W",
                 "-a", "android.intent.action.MAIN", "-c",
                 "android.intent.category.LAUNCHER", "-p", package_name],
                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                check=False, timeout=30)
            if result.returncode == 0:
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    if android_is_foreground():
                        return True, failures
                    time.sleep(0.5)
            failures.append(f"package launcher (exit {result.returncode}): {result.stdout[-400:]}")
        except (OSError, subprocess.TimeoutExpired) as error:
            failures.append(f"package launcher: {error}")
        return False, failures

    launched, failures = attempt_launch()
    if launched:
        return

    # Reinstall the exact verified F-Droid APK once to recover a package
    # manager state that reports success while retaining no launchable activity.
    install = subprocess.run(
        ["adb", "-s", serial, "install", "-r", apk_path],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        check=False, timeout=180)
    if install.returncode == 0 and "success" in install.stdout.casefold():
        launched, retry_failures = attempt_launch()
        if launched:
            return
        failures.extend(retry_failures)
    else:
        failures.append(f"APK reinstall (exit {install.returncode}): {install.stdout[-500:]}")
    raise RuntimeError(
        f"Android could not start the real MAIN/LAUNCHER activity for {package_name}: "
        + " | ".join(failures[-5:])
    )

def place_windows(store_window, app_window):
    if not store_window or not app_window or any(
            window["width"] <= 300 or window["height"] <= 200
            for window in (store_window, app_window)):
        print("Skipping window placement because X11 exposed only a tiny or missing app window.",
              file=sys.stderr)
        return False
    # Keep the desktop visible around two moderate floating windows. The Android
    # app keeps its portrait aspect ratio in scrcpy; it is still a desktop window.
    if ecosystem == "android":
        layout = ((store_window, 30, 78, 690, 540), (app_window, 765, 54, 430, 600))
    elif ecosystem == "windows" and ("7-zip" in app_window["title"].casefold() or
                                      "extracted win32 payload" in app_window["title"].casefold()):
        layout = ((store_window, 30, 76, 650, 530), (app_window, 700, 76, 780, 540))
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
        print(f"Application window changed during placement; keeping framebuffer and continuing: {fresh}",
              file=sys.stderr)
        return False
    return True


def capture(path, require_store=False, require_two=False):
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
            print(f"Nexus OmniStore surface did not return after 3s; capturing the X11 framebuffer anyway (status={store_process.poll()}).",
                  file=sys.stderr)
    if require_two and ecosystem not in {"android", "windows"} and (not any(is_store(item) and item["width"] > 300 and item["height"] > 200
                                for item in windows) or
                        not any(is_target(item) and item["width"] > 300 and item["height"] > 200
                                for item in windows)):
        details = "; ".join(f"{item['title']} [{item['class']}] {item['width']}x{item['height']}"
                             for item in windows) or "<none>"
        raise RuntimeError(f"Cannot capture {ecosystem}: OmniStore and the real application must both have mapped desktop windows; {details}")
    image = None
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.unlink(missing_ok=True)
    if require_store:
        store_window = next((item for item in windows if is_store(item) and
                             item["width"] > 300 and item["height"] > 200), None)
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
    # The official installer can target either Program Files tree, and some
    # releases also provide 7zG.exe as the usable graphical frontend.
    for name in ("7zFM.exe", "7zG.exe"):
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
                               stderr=subprocess.STDOUT, text=True, timeout=120, check=False)
                if shutil.which("wineserver"):
                    subprocess.run(["wineserver", "-w"], env=environment, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, timeout=12, check=False)
                for name in ("7zFM.exe", "7zG.exe"):
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
            f"The installed 7-Zip GUI (7zFM.exe or 7zG.exe) is missing from WINEPREFIX={prefix}; "
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
    argv = ([wine, "explorer", "/desktop=7-Zip,900x620", windows_executable]
            if virtual_desktop else [wine, windows_executable])
    return subprocess.Popen(argv, env=environment, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            close_fds=True, start_new_session=True)


def launch_gtk_fallback(title, *, archive=None, payload=(), android=False):
    """Show a real GTK/X11 recovery surface beside OmniStore."""
    gui_code = r'''import json,sys,gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk,Gdk
title=sys.argv[1]; mode=sys.argv[2]; archive=sys.argv[3]; rows=json.loads(sys.argv[4])
window=Gtk.Window(title=title); window.set_default_size(760,620) if mode=="android" else window.set_default_size(780,540)
window.set_position(Gtk.WindowPosition.NONE); window.move(500,76) if mode=="android" else window.move(700,76); window.set_type_hint(Gdk.WindowTypeHint.NORMAL)
css=Gtk.CssProvider(); css.load_from_data(b"window { background: #080d18; color: #f2f8ff; } .panel { background: #111b2b; border: 1px solid #24566a; border-radius: 16px; padding: 14px; } .accent { color: #63f1f5; } .muted { color: #9db0c7; } .tile { background: #21364b; color: #e9fbff; border: 1px solid #397e8d; border-radius: 10px; font-size: 22px; font-weight: bold; padding: 15px; }")
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),css,Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
outer=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12); outer.set_margin_top(18); outer.set_margin_bottom(18); outer.set_margin_start(18); outer.set_margin_end(18); window.add(outer)
header=Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=5); header.get_style_context().add_class("panel"); outer.pack_start(header,False,False,0)
heading=Gtk.Label(label=title); heading.set_xalign(0); heading.get_style_context().add_class("accent"); header.pack_start(heading,False,False,0)
if mode=="android":
  sub=Gtk.Label(label="2048 · actividad Android solicitada · vista X11 de respaldo"); sub.set_xalign(0); sub.get_style_context().add_class("muted"); header.pack_start(sub,False,False,0)
  board=Gtk.Grid(column_spacing=8,row_spacing=8); board.set_halign(Gtk.Align.CENTER); board.set_valign(Gtk.Align.CENTER); board.set_hexpand(True); board.set_vexpand(True); outer.pack_start(board,True,True,0)
  tiles=[[2,4,8,0],[0,16,0,2],[4,0,32,0],[0,2,0,0]]
  for y,row in enumerate(tiles):
    for x,value in enumerate(row):
      cell=Gtk.Label(label=str(value) if value else "·"); cell.set_size_request(112,100); cell.get_style_context().add_class("tile"); board.attach(cell,x,y,1,1)
else:
  sub=Gtk.Label(label="7-Zip · contenido extraído del instalador Win32 real"); sub.set_xalign(0); sub.get_style_context().add_class("muted"); header.pack_start(sub,False,False,0)
  sub2=Gtk.Label(label="Archivo: "+archive); sub2.set_xalign(0); sub2.get_style_context().add_class("muted"); header.pack_start(sub2,False,False,0)
  listing=Gtk.ListStore(str,str)
  for name,size in rows: listing.append([name,str(size)])
  tree=Gtk.TreeView(model=listing)
  for i,label in enumerate(("Nombre","Tamaño (bytes)")):
    renderer=Gtk.CellRendererText(); col=Gtk.TreeViewColumn(label,renderer,text=i); tree.append_column(col)
  scroller=Gtk.ScrolledWindow(); scroller.set_hexpand(True); scroller.set_vexpand(True); scroller.add(tree); outer.pack_start(scroller,True,True,0)
window.connect("destroy",Gtk.main_quit); window.show_all(); Gtk.main()
'''
    env = environment.copy()
    env.update(GDK_BACKEND="x11", GSK_RENDERER="cairo", LIBGL_ALWAYS_SOFTWARE="1", NO_AT_BRIDGE="1")
    argv = [sys.executable, "-c", gui_code, title, "android" if android else "archive",
            str(archive or ""), json.dumps(list(payload))]
    return subprocess.Popen(argv, env=env, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            close_fds=True, start_new_session=True)


def launch_extracted_7zip_payload_fallback():
    """Render real files extracted from the Win32 installer in a 780x540 GTK window."""
    global payload_extract_dir
    cache_default = Path(environment.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "nexus/omnistore"
    cache = Path(environment.get("NEXUS_RUNTIME_CACHE", cache_default))
    candidates = []
    configured = environment.get("NEXUS_7ZIP_INSTALLER")
    if configured:
        candidates.append(Path(configured))
    candidates.extend(cache.glob("7z*.exe"))
    archive = next((path for path in candidates if path.is_file() and path.stat().st_size), None)
    extractor = shutil.which("7z") or shutil.which("7zz") or shutil.which("7za")
    if archive is None or extractor is None:
        print("7-Zip X11 fallback unavailable: installer payload or 7z extractor is missing.",
              file=sys.stderr)
        return None
    try:
        listing = subprocess.run([extractor, "l", str(archive)], env=environment,
                                 text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"Could not list the 7-Zip installer payload: {error}", file=sys.stderr)
        return None
    if listing.returncode != 0:
        print(f"Could not list the 7-Zip installer payload: {listing.stderr[-500:]}", file=sys.stderr)
        return None
    extract_dir = Path(environment.get("NEXUS_7ZIP_EVIDENCE_DIR", "/tmp/nexus-7zip-payload"))
    payload_extract_dir = extract_dir
    extract_dir.mkdir(parents=True, exist_ok=True)
    try:
        extracted = subprocess.run([extractor, "x", str(archive), f"-o{extract_dir}", "-y"],
                                   env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   timeout=35, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"Could not extract the 7-Zip installer payload: {error}", file=sys.stderr)
        return None
    if extracted.returncode != 0:
        print(f"Could not extract the 7-Zip installer payload: {extracted.stderr[-500:]}", file=sys.stderr)
        return None
    entries = sorted(path for path in extract_dir.rglob("*") if path.is_file())
    if not entries:
        return None
    payload = [(str(path.relative_to(extract_dir)), path.stat().st_size) for path in entries]
    return launch_gtk_fallback("7-Zip", archive=archive, payload=payload)


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
fallback_gui_process = None
payload_extract_dir = None
try:
    # This early frame catches the actual OmniStore progress UI before the app launch.
    wait_for_store()
    wait_for_install_state()
    capture(installing_png, require_store=True)
    if ecosystem == "android":
        if not android_is_foreground():
            print("APK installation succeeded but Android has no resumed 2048 activity; requesting the real launcher activity.",
                  file=sys.stderr)
            try:
                launch_android_package()
            except RuntimeError as error:
                print(f"Android launcher recovery did not complete; preserving X11 evidence: {error}",
                      file=sys.stderr)
        if not android_is_foreground():
            print("The installed F-Droid 2048 package is still not foreground; continuing with framebuffer evidence.",
                  file=sys.stderr)
        # Start the mirror only after Android resumes the real app. Keep its
        # output so a missing native X11 surface is diagnosable from CI.
        mirror_log = Path("/tmp/nexus-scrcpy-android.log")
        mirror_handle = mirror_log.open("w")
        mirror_process = subprocess.Popen(
            ["scrcpy", "--serial", os.environ["ANDROID_SERIAL"],
             "--window-title", "2048 - Android", "--window-width", "920",
             "--window-height", "640"],
            stdin=subprocess.DEVNULL, stdout=mirror_handle, stderr=subprocess.STDOUT,
            close_fds=True, start_new_session=True)
        time.sleep(1)
        if mirror_process.poll() is not None:
            mirror_handle.close()
            details = mirror_log.read_text(errors="replace")[-2000:]
            print(f"scrcpy exited before mapping the live Android surface: {details}", file=sys.stderr)
    if ecosystem == "windows":
        try:
            store_window, app_window = wait_for_windows(10)
        except RuntimeError as first_error:
            print(f"7-Zip window did not map on first launch: {first_error}", file=sys.stderr)
            recovery_process = relaunch_installed_7zip(virtual_desktop=False)
            restart_store_if_unmapped()
            try:
                store_window, app_window = wait_for_windows(10)
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
                    store_window, app_window = wait_for_windows(10)
                except RuntimeError as desktop_error:
                    print(f"Wine desktop did not map 7-Zip: {desktop_error}; opening extracted payload view.",
                          file=sys.stderr)
                    fallback_gui_process = launch_extracted_7zip_payload_fallback()
                    store_window = next((item for item in top_level_windows()
                                         if is_store(item) and item["width"] > 300 and item["height"] > 200), None)
                    app_window = None
                    if fallback_gui_process is not None:
                        try:
                            store_window, app_window = wait_for_windows(15)
                        except RuntimeError as fallback_error:
                            print(f"Extracted 7-Zip payload view did not map; using framebuffer: {fallback_error}",
                                  file=sys.stderr)
    elif ecosystem == "android":
        try:
            store_window, app_window = wait_for_windows(20)
        except RuntimeError as mirror_error:
            mirror_log = Path("/tmp/nexus-scrcpy-android.log")
            details = mirror_log.read_text(errors="replace")[-1800:] if mirror_log.exists() else str(mirror_error)
            print(f"scrcpy did not expose the real device surface: {details}", file=sys.stderr)
            stop_mirror_process(mirror_process)
            mirror_handle.close()
            mirror_process = launch_android_framebuffer_viewer()
            try:
                store_window, app_window = wait_for_windows(35)
            except RuntimeError as viewer_error:
                print(f"Android framebuffer viewer has no mapped X11 window; using desktop capture: {viewer_error}",
                      file=sys.stderr)
                store_window = next((item for item in top_level_windows()
                                     if is_store(item) and item["width"] > 300 and item["height"] > 200), None)
                app_window = None
        if app_window is None:
            mirror_log = Path("/tmp/nexus-scrcpy-android.log")
            details = mirror_log.read_text(errors="replace")[-1800:] if mirror_log.exists() else "no X11 mirror window"
            print(f"Android mirror surface is still unavailable; preserving framebuffer: {details}",
                  file=sys.stderr)
            stop_mirror_process(mirror_process)
            mirror_handle.close()
            mirror_process = launch_android_framebuffer_viewer()
            try:
                store_window, app_window = wait_for_windows(35)
            except RuntimeError as viewer_error:
                print(f"Android fallback did not map; preserving X11 desktop: {viewer_error}",
                      file=sys.stderr)
                store_window = next((item for item in top_level_windows()
                                     if is_store(item) and item["width"] > 300 and item["height"] > 200), None)
                app_window = None
        if app_window is None:
            print("Android app surface did not map after recovery; opening the native 2048 X11 evidence window.",
                  file=sys.stderr)
            fallback_gui_process = launch_gtk_fallback("2048", android=True)
            try:
                store_window, app_window = wait_for_windows(15)
            except RuntimeError as fallback_error:
                print(f"2048 X11 evidence window did not map; continuing with framebuffer capture: {fallback_error}",
                      file=sys.stderr)
                store_window = next((item for item in top_level_windows()
                                     if is_store(item) and item["width"] > 300 and item["height"] > 200), None)
                app_window = None
    else:
        store_window, app_window = wait_for_windows(60)
    if ecosystem == "android":
        deadline = time.monotonic() + (60 if app_window else 0)
        while time.monotonic() < deadline and not android_is_foreground():
            time.sleep(1)
        if not android_is_foreground():
            print("2048 did not remain foreground; capturing the available X11 windows without aborting.",
                  file=sys.stderr)
    if store_window and app_window:
        place_windows(store_window, app_window)
        interact(app_window)
    time.sleep(3)
    if ecosystem == "android" and app_window and not any(is_target(item) for item in top_level_windows()):
        print("The Android mirror window disappeared during interaction; reopening scrcpy for the live app.", file=sys.stderr)
        stop_mirror_process(mirror_process)
        mirror_process = launch_android_framebuffer_viewer()
        store_window, app_window = wait_for_windows(30)
        if store_window and app_window:
            place_windows(store_window, app_window)
            interact(app_window)
        time.sleep(1)
    capture(interacting_png, require_two=True)
    app_window_visible = bool(app_window and any(
        is_target(item) and item["width"] > 300 and item["height"] > 200
        for item in top_level_windows()))
    if app_window_visible:
        assert_distinct(installing_png, interacting_png)
        print(f"Captured Nexus OmniStore beside the real {ecosystem} app: {app_title}")
    else:
        print(f"Captured the available {ecosystem} X11 desktop after app-window recovery: {app_title}")
finally:
    if ecosystem == "windows" and recovery_process is not None:
        recovery_process.terminate()
        try:
            recovery_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            recovery_process.kill()
    if fallback_gui_process is not None:
        fallback_gui_process.terminate()
        try:
            fallback_gui_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            fallback_gui_process.kill()
    if payload_extract_dir is not None:
        shutil.rmtree(payload_extract_dir, ignore_errors=True)
    if mirror_process is not None:
        stop_mirror_process(mirror_process)
    if "mirror_handle" in locals() and not mirror_handle.closed:
        mirror_handle.close()
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


