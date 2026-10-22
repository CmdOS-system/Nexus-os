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


def validate_live_window(ecosystem, window_id):
    """Inspect the mapped X11 window and its owner while the runtime is live."""
    if not os.environ.get("DISPLAY"):
        raise ValueError("live X11 identity check requires DISPLAY")
    if not shutil.which("xprop") or not shutil.which("wmctrl"):
        raise ValueError("live X11 identity check requires xprop and wmctrl")
    listing = subprocess.run(["wmctrl", "-lpG"], check=True, text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    row = next((line.split(None, 7) for line in listing.stdout.splitlines()
                if line.split(None, 1)[0] == window_id), None)
    if not row or len(row) < 7:
        raise ValueError(f"X11 window {window_id} is not present in wmctrl -lpG")
    pid = int(row[2])
    width, height = int(row[5]), int(row[6])
    if width < 300 or height < 200 or pid <= 1:
        raise ValueError(f"runtime window is tiny or has no process owner: {width}x{height}, pid={pid}")
    props = subprocess.run(["xprop", "-id", window_id, "WM_CLASS"], check=True,
                           text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5).stdout
    match = re.search(r'=\s*"([^"]+)"\s*,\s*"([^"]+)"', props)
    wm_class = " ".join(match.groups()).casefold() if match else ""
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
        "android": ("scrcpy",),
        # No Linux-hosted third-party IPA runtime/desktop bridge is configured.
        "ios": (),
    }[ecosystem]
    if not allowed or not any(token in identity for token in allowed):
        raise ValueError(f"unverified real-app owner: ecosystem={ecosystem}, WM_CLASS={wm_class!r}, pid={pid}, process={comm!r}")
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
