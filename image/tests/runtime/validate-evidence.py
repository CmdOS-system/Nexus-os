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
    """Read X11 geometry, WM_CLASS, and owner PID through Python-Xlib."""
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
        return int(geometry.width), int(geometry.height), pid, wm_class
    finally:
        connection.close()




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

    if "ffplay" not in identity:
        print(f"live Android package verified as foreground: {package} on {serial}")
        return
    title = subprocess.run(["xdotool", "getwindowname", window_id], text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=3, check=False).stdout.strip()
    if title != "Privacy Friendly 2048":
        raise ValueError(f"native Android viewer has unexpected title: {title!r}")
    lowered = cmdline.casefold()
    if "-loop 0" not in lowered or "/tmp/android-live.mp4" not in lowered:
        raise ValueError("ffplay is not looping the Android framebuffer video")
    image = Path("/tmp/android-live.png")
    if not image.is_file() or image.stat().st_size <= 4096 or image.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("the live Android framebuffer image is missing or incomplete")
    video = Path("/tmp/android-live.mp4")
    if not video.is_file() or video.stat().st_size < 4096:
        raise ValueError("the looping Android framebuffer video is missing or incomplete")
    process_table = subprocess.run(["ps", "-eo", "args="], text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   timeout=5, check=False).stdout
    if "android-screencap-viewer.sh" not in process_table:
        raise ValueError("native viewer is not owned by the active Android screenshot stream helper")
    print(f"live Android APK and looping ffplay framebuffer verified: {package} on {serial}")

def validate_live_window(ecosystem, window_id):
    """Inspect the mapped X11 window and its owner while the runtime is live."""
    if not os.environ.get("DISPLAY"):
        raise ValueError("live X11 identity check requires DISPLAY")
    if shutil.which("xprop") and shutil.which("wmctrl"):
        listing = subprocess.run(["wmctrl", "-lpG"], check=True, text=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        row = next((line.split(None, 7) for line in listing.stdout.splitlines()
                    if line.split(None, 1)[0] == window_id), None)
        if not row or len(row) < 7:
            raise ValueError(f"X11 window {window_id} is not present in wmctrl -lpG")
        pid = int(row[2])
        width, height = int(row[5]), int(row[6])
        props = subprocess.run(["xprop", "-id", window_id, "WM_CLASS"], check=True,
                               text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5).stdout
        match = re.search(r'=\s*"([^"]+)"\s*,\s*"([^"]+)"', props)
        wm_class = " ".join(match.groups()).casefold() if match else ""
    else:
        width, height, pid, wm_class = native_x11_window(window_id)
    if width < 300 or height < 200 or pid <= 1:
        raise ValueError(f"runtime window is tiny or has no process owner: {width}x{height}, pid={pid}")
    cmdline_path = Path(f"/proc/{pid}/cmdline")
    cmdline = cmdline_path.read_bytes().replace(b"\0", b" ").decode(errors="replace").casefold() if cmdline_path.exists() else ""
    comm_path = Path(f"/proc/{pid}/comm")
    comm = comm_path.read_text(errors="replace").strip().casefold() if comm_path.exists() else ""
    identity = f"{wm_class} {cmdline} {comm}"
    if "python" in identity or "omni-store.py" in identity or "omni-store" in identity:
        raise ValueError(f"synthetic/store-owned app window rejected: WM_CLASS={wm_class!r}, pid={pid}, process={comm!r}")

    allowed = {
        "linux": ("gnome-mines", "org.gnome.mines", "galculator", "vlc"),
        "windows": ("7zfm.exe", "7zfm", "explorer.exe"),
        "web": ("chromium", "chromium-browser", "chrome"),
        "android": ("scrcpy", "ffplay"),
        # No Linux-hosted third-party IPA runtime/desktop bridge is configured.
        "ios": (),
    }[ecosystem]
    if not allowed or not any(token in identity for token in allowed):
        raise ValueError(f"unverified real-app owner: ecosystem={ecosystem}, WM_CLASS={wm_class!r}, pid={pid}, process={comm!r}")
    if ecosystem == "android":
        _validate_android_app_and_viewer(identity, cmdline, pid, window_id)
    if ecosystem == "windows":
        # Wine often assigns the visible X11 surface to explorer.exe. Also
        # require the official installed GUI process to be live in that prefix.
        process_table = subprocess.run(["ps", "-eo", "args="], check=True, text=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5).stdout.casefold()
        if "7zfm.exe" not in process_table:
            raise ValueError("the Wine window is mapped but the real 7zFM.exe process is not running")
    print(f"live X11 owner verified: ecosystem={ecosystem} id={window_id} pid={pid} WM_CLASS={wm_class}")


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
