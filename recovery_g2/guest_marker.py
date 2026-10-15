"""UEFI guest success marker: never confuse process liveness with boot success.

QEMU's isa-debug-exit device returns (guest_value << 1) | 1.
The Nexus probe uses guest_value=0x2a and expects process exit 0x55.
"""
SUCCESS_GUEST_VALUE = 0x2A
SUCCESS_EXIT_CODE = (SUCCESS_GUEST_VALUE << 1) | 1


def classify_guest_exit(returncode, *, timed_out=False):
    if timed_out:
        return {"status": "inconclusive_timeout", "guest_marker_seen": False}
    if type(returncode) is not int:
        raise ValueError("returncode must be an integer")
    if returncode == SUCCESS_EXIT_CODE:
        return {"status": "guest_marker_confirmed", "guest_marker_seen": True}
    return {"status": "guest_not_confirmed", "guest_marker_seen": False,
            "returncode": returncode}
