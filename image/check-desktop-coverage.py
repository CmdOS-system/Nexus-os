"""Reject large near-black regions in Nexus aurora desktop captures.

This heuristic supplements visual review; it cannot identify Horizon or prove UI
usability. Intentionally black wallpaper is outside this acceptance criterion.
"""
import argparse
import json
from PIL import Image


def inspect(path):
    with Image.open(path) as source:
        image = source.convert("RGB")
    if image.width < 320 or image.height < 200:
        raise ValueError("Desktop capture is smaller than 320x200")
    empty = []
    for row in range(6):
        for column in range(8):
            tile = image.crop((column * image.width // 8,
                               row * image.height // 6,
                               (column + 1) * image.width // 8,
                               (row + 1) * image.height // 6))
            pixels = getattr(tile, "get_flattened_data", tile.getdata)()
            lit = sum(max(pixel) > 8 for pixel in pixels)
            if lit / (tile.width * tile.height) < 0.005:
                empty.append([column, row])
    return {"path": str(path), "size": image.size, "near_black_tiles": empty,
            "passed": len(empty) < 4}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+")
    args = parser.parse_args()
    results = [inspect(path) for path in args.images]
    print(json.dumps(results, indent=2))
    raise SystemExit(0 if all(result["passed"] for result in results) else 1)
