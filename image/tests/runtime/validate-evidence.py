#!/usr/bin/env python3
"""Fail closed on missing, tiny, black, or duplicated runtime evidence PNGs."""
import argparse
import hashlib
import math
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
    if len(data) < 15 * 1024:
        raise ValueError(f"PNG under 15 KB ({len(data)} bytes)")
    width, height, mean, nonblack = png_pixels(data)
    if width < 320 or height < 200 or mean < 5 or nonblack < 0.03:
        raise ValueError(f"black/empty/undersized image: {width}x{height}, mean={mean:.1f}, nonblack={nonblack:.1%}")
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, default=Path("evidence"))
    parser.add_argument("--ecosystems", nargs="+", choices=[*PAIRS, "all"], default=["all"])
    args = parser.parse_args()
    ecosystems = list(PAIRS) if "all" in args.ecosystems else args.ecosystems
    for ecosystem in ecosystems:
        installing, interacting, primary, video = PAIRS[ecosystem]
        folder = args.evidence_root / ecosystem
        first, second, running, movie = (folder / installing, folder / interacting,
                                         folder / primary, folder / video)
        if not first.is_file() or not second.is_file():
            raise SystemExit(f"{ecosystem}: missing required PNG: {first if not first.is_file() else second}")
        pngs = sorted(folder.glob("*.png"))
        if not pngs:
            raise SystemExit(f"{ecosystem}: no PNG evidence found in {folder}")
        hashes = {path: validate_png(path) for path in pngs}
        first_hash, second_hash = hashes[first], hashes[second]
        if first_hash == second_hash:
            raise SystemExit(f"{ecosystem}: installing/interacting SHA256 is identical: {first}")
        if not running.is_file():
            raise SystemExit(f"{ecosystem}: missing primary running PNG: {running}")
        if running not in hashes:
            running_hash = validate_png(running)
        else:
            running_hash = hashes[running]
        if ecosystem == "ios" and running_hash in {first_hash, second_hash}:
            raise SystemExit("ios: installing/interacting/running PNG captures must all be distinct")
        if not movie.is_file() or movie.stat().st_size < 15 * 1024:
            raise SystemExit(f"{ecosystem}: missing or too-small MP4: {movie}")
        print(f"{ecosystem}: PNGs valid and distinct; MP4 {movie.stat().st_size} bytes")

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, zlib.error, struct.error) as error:
        raise SystemExit(f"evidence validation failed: {error}")
