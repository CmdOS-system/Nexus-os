"""Simulate Recovery G2 boot cycles without modifying host disks."""
import argparse
import json
import tempfile
from recovery_g2.boot_state import BootState
from recovery_g2.controller import RecoveryController

def simulate(attempts=3, healthy_on=None):
    if not 1 <= attempts <= 10:
        raise ValueError("attempts must be between 1 and 10")
    if healthy_on is not None and not 1 <= healthy_on <= attempts:
        raise ValueError("healthy_on must refer to a candidate attempt")
    events = []
    with tempfile.TemporaryDirectory(prefix="nexus-recovery-") as directory:
        controller = RecoveryController(directory)
        controller.store.save(BootState())
        controller.stage_verified("B", authenticated=True, image_durable=True,
                                  attempts=attempts)
        for number in range(1, attempts + 2):
            controller = RecoveryController(directory)
            selected = controller.prepare_boot()
            events.append({"cycle": number, "selected": selected,
                           "remaining": controller.store.load().attempts_left})
            if selected == "A":
                break
            if healthy_on == number:
                controller.confirm_health("B", healthy=True)
                events.append({"event": "confirmed", "slot": "B"})
                break
        final = RecoveryController(directory).store.load()
        return {"events": events, "confirmed": final.confirmed,
                "pending": final.candidate}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--healthy-on", type=int)
    args = parser.parse_args()
    print(json.dumps(simulate(args.attempts, args.healthy_on), indent=2))
