#!/usr/bin/env python3
"""Generate a brief, clean Nexus tone and play it when audio is available."""
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import wave

RATE = 22050
MELODIES = {
    "boot": ((523.25, 0.12), (659.25, 0.12), (783.99, 0.22)),
    "invoke": ((659.25, 0.07), (880.00, 0.10)),
    "launcher": ((587.33, 0.08), (783.99, 0.11)),
}


def render(event):
    pieces = []
    for frequency, duration in MELODIES.get(event, MELODIES["invoke"]):
        count = int(RATE * duration)
        for index in range(count):
            edge = min(index / (RATE * 0.012), (count - index) / (RATE * 0.024), 1.0)
            envelope = max(0.0, edge) ** 0.7
            sample = int(10500 * envelope * math.sin(2 * math.pi * frequency * index / RATE))
            pieces.append(struct.pack("<h", sample))
        pieces.append(b"\0\0" * int(RATE * 0.025))
    return b"".join(pieces)


def main():
    event = sys.argv[1] if len(sys.argv) > 1 else "invoke"
    if sys.argv[1:] and sys.argv[1] not in MELODIES:
        return 0
    players = [path for path in (shutil.which("paplay"), shutil.which("aplay")) if path]
    if not players:
        return 0
    with tempfile.NamedTemporaryFile(prefix="nexus-tone-", suffix=".wav") as audio:
        with wave.open(audio.name, "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(RATE)
            output.writeframes(render(event))
        for player in players:
            try:
                result = subprocess.run([player, audio.name], stdin=subprocess.DEVNULL,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                        timeout=3, check=False)
                if result.returncode == 0:
                    break
            except (OSError, subprocess.TimeoutExpired):
                continue
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
