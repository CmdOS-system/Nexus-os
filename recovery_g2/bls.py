"""Boot Loader Specification Type #1 entry naming (offline only).

This module never modifies EFI partitions or invokes bootctl.
"""
import re

_ENTRY = re.compile(r"^(?P<name>[A-Za-z0-9][A-Za-z0-9_.-]*?)(?:\+(?P<left>[0-9]+)(?:-(?P<done>[0-9]+))?)?\.conf$")

def parse_entry(filename):
    if not isinstance(filename, str):
        raise ValueError("entry filename must be a string")
    match = _ENTRY.fullmatch(filename)
    if match is None:
        raise ValueError("invalid boot entry filename")
    left = match.group("left")
    done = match.group("done")
    return {
        "name": match.group("name"),
        "tries_left": None if left is None else int(left),
        "tries_done": None if done is None else int(done),
    }

def tentative_entry(name, tries=3):
    if type(tries) is not int or not 1 <= tries <= 10:
        raise ValueError("invalid boot attempt budget")
    parsed = parse_entry(name + ".conf")
    if parsed["tries_left"] is not None:
        raise ValueError("entry is already tentative")
    return f"{name}+{tries}.conf"

def entry_status(filename):
    """Return BLS assessment status without touching the EFI partition."""
    entry = parse_entry(filename)
    if entry["tries_left"] is None:
        return "good"
    return "bad" if entry["tries_left"] == 0 else "indeterminate"

def after_boot_attempt(filename):
    """Model systemd-boot's rename BEFORE launching the selected kernel."""
    entry = parse_entry(filename)
    left = entry["tries_left"]
    if left is None or left == 0:
        raise ValueError("entry has no remaining counted attempts")
    done = entry["tries_done"] or 0
    return f'{entry["name"]}+{left - 1}-{done + 1}.conf'

def bless_entry(filename):
    """Model systemd-bless-boot after successful health assessment."""
    entry = parse_entry(filename)
    if entry["tries_left"] is None:
        raise ValueError("entry is not counted")
    return entry["name"] + ".conf"
