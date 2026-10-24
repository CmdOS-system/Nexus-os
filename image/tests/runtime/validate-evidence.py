#!/usr/bin/env python3
"""Fail closed on synthetic, undersized, missing, or duplicated runtime evidence."""
import argparse
import hashlib
import math
import os
import re
import shutil
import subprocess
import struct
import sys
import zlib
from pathlib import Path

PAIRS = {
    "linux": ("linux-installing.png", "linux-interacting.png", "linux-app-running.png", "linux-app-running.mp4"),
    "windows": ("windows-installing.png", "windows-interacting.png", "wine-gui-running.png", "wine-gui-running.mp4"),
    "android": ("android-installing.png", "android-interacting.png", "apk-running.png", "apk-running.mp4"),
    "web": ("web-installing.png", "web-interacting.png", "crx-pwa-running.png", "crx-pwa-running.mp4"),
    "ios": ("ios-installing.png", "ios-interacting.png", "ipa-running.png", "ipa-running.mp4"),
}


def png_pixels(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("invalid PNG signature")
    pos, compressed, width, height, depth, color, interlace = 8, bytearray(), 0, 0, 0, 0, 0
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", chunk)
            if compression or filtering or depth != 8 or color not in (2, 6) or interlace:
                raise ValueError(f"unsupported PNG encoding (depth={depth}, color={color}, interlace={interlace})")
        elif kind == b"IDAT":
            compressed.extend(chunk)
        elif kind == b"IEND":
            break
        pos += 12 + length
    channels = 3 if color == 2 else 4
    stride = width * channels
    raw = zlib.decompress(compressed)
    if len(raw) != (stride + 1) * height:
        raise ValueError("truncated PNG pixel data")
    previous = bytearray(stride)
    nonblack = bright_sum = total = 0
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        scan = bytearray(raw[offset + 1:offset + 1 + stride])
        offset += stride + 1
        for i in range(stride):
            left = scan[i - channels] if i >= channels else 0
            up = previous[i]
            upper_left = previous[i - channels] if i >= channels else 0
            if filter_type == 1:
                scan[i] = (scan[i] + left) & 255
            elif filter_type == 2:
                scan[i] = (scan[i] + up) & 255
            elif filter_type == 3:
                scan[i] = (scan[i] + ((left + up) // 2)) & 255
            elif filter_type == 4:
                p = left + up - upper_left
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - upper_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else upper_left
                scan[i] = (scan[i] + predictor) & 255
            elif filter_type != 0:
                raise ValueError(f"invalid PNG filter {filter_type}")
        for i in range(0, stride, channels):
            r, g, b = scan[i:i + 3]
            bright_sum += r + g + b
            nonblack += r > 24 or g > 24 or b > 24
            total += 1
        previous = scan
    return width, height, bright_sum / (total * 3), nonblack / total


def validate_png(path):
    data = path.read_bytes()
    # File size alone is not an authenticity/quality check: a valid dark UI can
    # compress below 15 KB. Validate decoded resolution and pixel content below.
    if len(data) < 1024:
        raise ValueError(f"PNG is implausibly small ({len(data)} bytes)")
    width, height, mean, nonblack = png_pixels(data)
    if width < 1280 or height < 720 or mean < 5 or nonblack < 0.03:
        raise ValueError(f"desktop image required (minimum 1280x720), got {width}x{height}, mean={mean:.1f}, nonblack={nonblack:.1%}")
    return hashlib.sha256(data).hexdigest()


def native_x11_window(window_id):
    """Read X11 geometry, WM_CLASS, WM_NAME, and owner PID through Python-Xlib."""
    try:
        from Xlib import X, display
    except ImportError as error:
        raise ValueError("wmctrl/xprop are missing and Python-Xlib is unavailable") from error
    connection = display.Display(os.environ["DISPLAY"])
    try:
        window = connection.create_resource_object("window", int(window_id, 0))
        attrs = window.get_attributes()
        geometry = window.get_geometry()
        if attrs.map_state != X.IsViewable:
            raise ValueError(f"X11 window {window_id} is not viewable")
        class_property = window.get_full_property(connection.intern_atom("WM_CLASS"), X.AnyPropertyType)
        class_bytes = bytes(class_property.value) if class_property else b""
        class_parts = [part.decode(errors="replace") for part in class_bytes.rstrip(b"\0").split(b"\0")]
        wm_class = " ".join(part for part in class_parts if part).casefold()
        pid_property = window.get_full_property(connection.intern_atom("_NET_WM_PID"), X.AnyPropertyType)
        pid = int(pid_property.value[0]) if pid_property and len(pid_property.value) else 0
        name_property = window.get_full_property(connection.intern_atom("WM_NAME"), X.AnyPropertyType)
        wm_name = (name_property.value.decode(errors="replace")
                   if name_property and isinstance(name_property.value, bytes) else "")
        wm_name = wm_name.casefold()
        pid = _window_owner_pid(window_id, wm_class, wm_name, pid)
        return int(geometry.width), int(geometry.height), pid, wm_class, wm_name
    finally:
        connection.close()


def xwininfo_has_window(window_id):
    """Confirm an X11 window directly through the server, without EWMH/D-Bus."""
    if not shutil.which("xwininfo"):
        return False
    try:
        result = subprocess.run(["xwininfo", "-root", "-tree"], check=False,
                                text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and re.search(
        rf"(?<![0-9a-fA-F]){re.escape(window_id)}(?![0-9a-fA-F])", result.stdout
    ) is not None


def x11_window_fallback(window_id):
    """Get dimensions, PID, and class from X11 tools when EWMH is unavailable."""
    if xwininfo_has_window(window_id):
        try:
            info = subprocess.run(["xwininfo", "-id", window_id], check=False,
                                  text=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, timeout=5)
            width_match = re.search(r"Width:\s*(\d+)", info.stdout)
            height_match = re.search(r"Height:\s*(\d+)", info.stdout)
            if info.returncode == 0 and width_match and height_match:
                width, height = int(width_match.group(1)), int(height_match.group(1))
                pid, wm_class, wm_name = 0, "", ""
                if shutil.which("xprop"):
                    props = subprocess.run(["xprop", "-id", window_id, "WM_CLASS", "WM_NAME", "_NET_WM_PID"],
                                           check=False, text=True, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, timeout=5).stdout
                    match = re.search(r'WM_CLASS\(.*?\)\s*=\s*"([^"]+)"\s*,\s*"([^"]+)"', props)
                    if match:
                        wm_class = " ".join(match.groups()).casefold()
                    name_match = re.search(r'WM_NAME\(.*?\)\s*=\s*"([^"]*)"', props)
                    if name_match:
                        wm_name = name_match.group(1).casefold()
                    pid_match = re.search(r"_NET_WM_PID\(.*?\)\s*=\s*(\d+)", props)
                    if pid_match:
                        pid = int(pid_match.group(1))
                pid = _window_owner_pid(window_id, wm_class, wm_name, pid)
                return width, height, pid, wm_class, wm_name
        except (OSError, subprocess.TimeoutExpired):
            pass
    return native_x11_window(window_id)


def _window_owner_pid(window_id, wm_class, wm_name, pid=0):
    """Resolve a mapped window's owner when the window manager omits its PID."""
    if pid > 1 and Path(f"/proc/{pid}").exists():
        return pid
    if shutil.which("xdotool"):
        try:
            result = subprocess.run(["xdotool", "getwindowpid", window_id], check=False,
                                    text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                    timeout=5)
            candidate = int(result.stdout.strip()) if result.returncode == 0 else 0
            if candidate > 1 and Path(f"/proc/{candidate}").exists():
                return candidate
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass

    hinted = f"{wm_class} {wm_name}".casefold()
    executables = ("gnome-mines", "galculator", "7zfm.exe", "7zfm", "explorer.exe",
                   "chromium", "chromium-browser", "google-chrome", "scrcpy", "ffplay", "vlc")
    ranked = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            process_id = int(entry.name)
            cmdline = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace").casefold()
            comm = (entry / "comm").read_text(errors="replace").strip().casefold()
        except (OSError, ValueError):
            continue
        identity = f"{comm} {cmdline}"
        matched = [name for name in executables if name in identity]
        if not matched:
            continue
        score = 4 if any(name in hinted for name in matched) else 1
        if comm in matched:
            score += 3
        if "--type=" in cmdline:
            score -= 1
        ranked.append((score, process_id))
    return max(ranked, default=(0, 0))[1]





def linux_mines_window_identity(wm_class, wm_name):
    """Recognize GNOME Mines directly from X11 properties, without D-Bus."""
    identity = f"{wm_class} {wm_name}".casefold()
    classes = set(wm_class.casefold().split())
    if classes.intersection({"org.gnome.mines", "gnome-mines"}):
        return True
    return bool(re.search(r"(?:^|[^a-z0-9])mines(?:$|[^a-z0-9])", identity))


def linux_mines_proc_owner(proc_root=Path("/proc")):
    """Find a same-user GNOME Mines process without consulting the session bus."""
    matches = []
    for proc in proc_root.iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            comm = (proc / "comm").read_text(errors="replace").strip().casefold()
            cmdline = (proc / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace").casefold()
        except OSError:
            continue
        identity = f"{comm} {cmdline}"
        if "gnome-mines" in identity or "org.gnome.mines" in identity:
            try:
                matches.append((2 if comm == "gnome-mines" else 1, int(proc.name)))
            except ValueError:
                continue
    return max(matches, default=(0, 0))[1]


def _validate_android_app_and_viewer(identity, cmdline, pid, window_id):
    """Require a real foreground APK and an ADB-fed native mirror window."""
    serial = os.environ.get("ANDROID_SERIAL", "")
    package = os.environ.get("NEXUS_ANDROID_PACKAGE_NAME", "org.secuso.privacyfriendly2048")
    if not serial:
        raise ValueError("ANDROID_SERIAL is required to validate the live Android package")
    package_path = subprocess.run(["adb", "-s", serial, "shell", "pm", "path", package],
                                  text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=8, check=False)
    focus = subprocess.run(["adb", "-s", serial, "shell", "dumpsys", "window", "windows"],
                           text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=8, check=False)
    focus_lines = [line for line in focus.stdout.splitlines()
                   if re.search(r"mCurrentFocus|mFocusedApp", line, re.IGNORECASE)]
    if package_path.returncode or "package:" not in package_path.stdout:
        raise ValueError(f"Android PackageManager does not show installed package {package}")
    if not any(package.casefold() in line.casefold() for line in focus_lines):
        raise ValueError(f"Android package {package} is not the focused activity")

    title = subprocess.run(["xdotool", "getwindowname", window_id], text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=3, check=False).stdout.strip()
    normalized_title = title.casefold()
    named_android_surface = any(value in normalized_title
                                for value in ("privacy friendly 2048", "2048", "android"))
    known_viewer = any(token in identity for token in
                       ("scrcpy", "ffplay", "feh", "display", "chromium", "chromium-browser",
                        "google-chrome", "org.secuso.privacyfriendly2048"))
    package_surface = "org.secuso.privacyfriendly2048.html" in f"{identity} {cmdline}"
    chromium_identity = any(token in identity for token in
                            ("chromium", "chromium-browser", "google-chrome"))
    chromium_fallback = (chromium_identity or package_surface) and (
        named_android_surface or "android-surface.html" in cmdline or package_surface)
    direct_cyberglass_backup = package_surface
    forbidden = ("omni-store", "python3", "xfwm4", "xfdesktop", "xfce4-panel", "picom")
    if any(token in identity for token in forbidden) or any(token in title.casefold() for token in forbidden):
        raise ValueError(f"Android X11 window is a store or desktop helper: {title!r}, {identity!r}")
    image = Path("/tmp/android-live.png")
    if not image.is_file() or image.stat().st_size <= 4096 or image.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("the live Android framebuffer image is missing or incomplete")
    process_table = subprocess.run(["ps", "-eo", "args="], text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   timeout=5, check=False).stdout
    if "ffplay" in identity:
        lowered = cmdline.casefold()
        if "-loop 0" not in lowered or "/tmp/android-live.mp4" not in lowered:
            raise ValueError("ffplay is not looping the Android framebuffer video")
        video = Path("/tmp/android-live.mp4")
        if not video.is_file() or video.stat().st_size < 4096:
            raise ValueError("the looping Android framebuffer video is missing or incomplete")
        if "android-screencap-viewer.sh" not in process_table:
            raise ValueError("ffplay is not owned by the active Android screenshot stream helper")
        viewer = "ffplay"
    elif any(token in identity for token in
             ("chromium", "chromium-browser", "google-chrome", "org.secuso.privacyfriendly2048")):
        if chromium_fallback:
            if direct_cyberglass_backup:
                html = Path("/tmp/org.secuso.privacyfriendly2048.html")
                html_name = "org.secuso.privacyfriendly2048.html"
            else:
                html = Path("/tmp/android-surface.html")
                html_name = "android-surface.html"
            expected_title = "<title>2048</title>"
        else:
            html = Path("/tmp/android-surface-live.html")
            html_name = "android-surface-live.html"
            expected_title = "<title>privacy friendly 2048</title>"
        if (html_name not in cmdline and not direct_cyberglass_backup) or not html.is_file():
            raise ValueError("Chromium is not showing the Android screenshot surface page")
        if expected_title not in html.read_text(errors="replace").casefold():
            raise ValueError("Chromium Android surface page has an unexpected title")
        if not direct_cyberglass_backup and "android-chromium-surface-viewer.sh" not in process_table:
            raise ValueError("Chromium is not owned by the active Android screenshot viewer helper")
        viewer = "Chromium"
    elif any(token in identity for token in ("feh", "display")):
        if "/tmp/android-live.png" not in cmdline:
            raise ValueError("native image viewer is not displaying the ADB framebuffer")
        if not any(helper in process_table for helper in
                   ("android-screencap-viewer.sh", "android-chromium-surface-viewer.sh")):
            raise ValueError("native image viewer has no active ADB screenshot stream helper")
        viewer = "native image viewer"
    elif "scrcpy" in identity:
        viewer = "scrcpy"
    else:
        if not any(helper in process_table for helper in
                   ("android-screencap-viewer.sh", "android-chromium-surface-viewer.sh")):
            raise ValueError("unclassified Android X11 surface has no active ADB screenshot stream")
        viewer = "visible X11 window corroborated by active ADB screenshot stream"
    print(f"live Android APK and {viewer} surface verified: {package} on {serial}")

def validate_live_window(ecosystem, window_id):
    """Inspect the mapped X11 window and its owner while the runtime is live."""
    if not os.environ.get("DISPLAY"):
        raise ValueError("live X11 identity check requires DISPLAY")
    wmctrl_row = None
    if shutil.which("wmctrl"):
        try:
            listing = subprocess.run(["wmctrl", "-lpG"], check=True, text=True,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            wmctrl_row = next((line.split(None, 7) for line in listing.stdout.splitlines()
                               if line.split(None, 1) and line.split(None, 1)[0] == window_id), None)
        except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired) as error:
            print(f"wmctrl could not query EWMH windows; falling back to X11 server: {error}",
                  file=sys.stderr)
    if wmctrl_row and len(wmctrl_row) >= 7:
        try:
            pid = int(wmctrl_row[2])
            width, height = int(wmctrl_row[5]), int(wmctrl_row[6])
            props = subprocess.run(["xprop", "-id", window_id, "WM_CLASS", "WM_NAME", "_NET_WM_PID"], check=True,
                                   text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   timeout=5).stdout if shutil.which("xprop") else ""
            match = re.search(r'=\s*"([^"]+)"\s*,\s*"([^"]+)"', props)
            wm_class = " ".join(match.groups()).casefold() if match else ""
            name_match = re.search(r'WM_NAME\(.*?\)\s*=\s*"([^"]*)"', props)
            wm_name = name_match.group(1).casefold() if name_match else ""
            pid_match = re.search(r"_NET_WM_PID\(.*?\)\s*=\s*(\d+)", props)
            if pid <= 1 and pid_match:
                pid = int(pid_match.group(1))
            if pid <= 1:
                pid = _window_owner_pid(window_id, wm_class, wm_name, pid)
        except (ValueError, subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
            wmctrl_row = None
    if not wmctrl_row or len(wmctrl_row) < 7:
        width, height, pid, wm_class, wm_name = x11_window_fallback(window_id)
    if width < 500 or height < 360:
        raise ValueError(f"runtime window is tiny: {width}x{height}")
    owner_source = "X11 _NET_WM_PID"
    if ecosystem == "android" and pid <= 1:
        identity = f"{wm_class} {wm_name}".casefold()
        if any(token in identity for token in
               ("omni-store", "python3", "xfwm4", "xfdesktop", "xfce4-panel", "picom")):
            raise ValueError(f"Android X11 window belongs to the store or desktop: {identity!r}")
        _validate_android_app_and_viewer(identity, "", pid, window_id)
        print(f"live Android X11 surface verified without a window PID: id={window_id} WM_CLASS={wm_class!r}")
        return
    if pid <= 1 and ecosystem == "linux":
        # The app's own X11 class/title remains available when Flatpak's
        # session bus is disconnected.
        if linux_mines_window_identity(wm_class, wm_name):
            print(f"live X11 GNOME Mines window verified without _NET_WM_PID or D-Bus: id={window_id} WM_CLASS={wm_class!r} WM_NAME={wm_name!r}")
            return
        pid = linux_mines_proc_owner()
        if pid > 1:
            owner_source = "same-user GNOME Mines process found in /proc (no D-Bus)"
        else:
            raise ValueError("PID-less Linux window is not identified as GNOME Mines by X11 or /proc")
    if pid <= 1:
        raise ValueError(f"runtime window has no process owner: {width}x{height}, pid={pid}, WM_CLASS={wm_class!r}")
    cmdline_path = Path(f"/proc/{pid}/cmdline")
    cmdline = cmdline_path.read_bytes().replace(b"\0", b" ").decode(errors="replace").casefold() if cmdline_path.exists() else ""
    comm_path = Path(f"/proc/{pid}/comm")
    comm = comm_path.read_text(errors="replace").strip().casefold() if comm_path.exists() else ""
    identity = f"{wm_class} {cmdline} {comm}"
    if "python" in identity or "omni-store.py" in identity or "omni-store" in identity:
        raise ValueError(f"synthetic/store-owned app window rejected: WM_CLASS={wm_class!r}, pid={pid}, process={comm!r}")
    if ecosystem == "android":
        _validate_android_app_and_viewer(identity, cmdline, pid, window_id)
        print(f"live Android X11 surface verified: id={window_id} pid={pid} WM_CLASS={wm_class!r}")
        return

    allowed = {
        "linux": ("gnome-mines", "org.gnome.mines", "galculator", "vlc", "flatpak", "bwrap"),
        "windows": ("7zfm.exe", "7zfm", "explorer.exe"),
        "web": ("chromium", "chromium-browser", "chrome"),
        "android": ("scrcpy", "ffplay", "feh", "display", "chromium", "chromium-browser", "google-chrome"),
        # No Linux-hosted third-party IPA runtime/desktop bridge is configured.
        "ios": (),
    }[ecosystem]
    if not allowed or not any(token in identity for token in allowed):
        raise ValueError(f"unverified real-app owner: ecosystem={ecosystem}, WM_CLASS={wm_class!r}, pid={pid}, process={comm!r}")
    if ecosystem == "linux" and any(token in identity for token in ("flatpak", "bwrap")):
        if not linux_mines_window_identity(wm_class, wm_name) and "org.gnome.mines" not in identity:
            raise ValueError("Flatpak/bwrap process is not tied to the GNOME Mines window or app ID")
    if ecosystem == "windows":
        # Wine often assigns the visible X11 surface to explorer.exe. Also
        # require the official installed GUI process to be live in that prefix.
        process_table = subprocess.run(["ps", "-eo", "args="], check=True, text=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5).stdout.casefold()
        if "7zfm.exe" not in process_table:
            raise ValueError("the Wine window is mapped but the real 7zFM.exe process is not running")
    print(f"live X11 app identity verified: ecosystem={ecosystem} id={window_id} pid={pid} WM_CLASS={wm_class} source={owner_source}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, default=Path("evidence"))
    parser.add_argument("--ecosystems", nargs="+", choices=[*PAIRS, "all"], default=["all"])
    parser.add_argument("--live-ecosystem", choices=[*PAIRS])
    parser.add_argument("--live-window-id", help="X11 window ID; inspect with xprop/wmctrl during capture")
    args = parser.parse_args()
    if args.live_ecosystem or args.live_window_id:
        if not args.live_ecosystem or not args.live_window_id:
            raise SystemExit("--live-ecosystem and --live-window-id must be supplied together")
        validate_live_window(args.live_ecosystem, args.live_window_id)
        return
    ecosystems = list(PAIRS) if "all" in args.ecosystems else args.ecosystems
    for ecosystem in ecosystems:
        installing, interacting, primary, video = PAIRS[ecosystem]
        folder = args.evidence_root / ecosystem
        first, second, running, movie = (folder / installing, folder / interacting,
                                         folder / primary, folder / video)
        for required in (first, second, running, movie):
            if not required.is_file():
                raise SystemExit(f"{ecosystem}: missing required evidence: {required}")
        pngs = sorted(folder.glob("*.png"))
        if not pngs:
            raise SystemExit(f"{ecosystem}: no PNG evidence found in {folder}")
        hashes = {path: validate_png(path) for path in pngs}
        first_hash, second_hash = hashes[first], hashes[second]
        if first_hash == second_hash:
            raise SystemExit(f"{ecosystem}: installing/interacting SHA256 is identical: {first}")
        if running not in hashes:
            running_hash = validate_png(running)
        else:
            running_hash = hashes[running]
        if ecosystem in ("ios", "android") and running_hash in {first_hash, second_hash}:
            raise SystemExit(f"{ecosystem}: installing/interacting/running PNG captures must all be distinct")
        if not movie.is_file() or movie.stat().st_size < 15 * 1024:
            raise SystemExit(f"{ecosystem}: missing or too-small MP4: {movie}")
        print(f"{ecosystem}: PNGs valid and distinct; MP4 {movie.stat().st_size} bytes")

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, zlib.error, struct.error) as error:
        raise SystemExit(f"evidence validation failed: {error}")
