#!/usr/bin/env python3
"""Nexus Recovery A/B state-machine simulator.

Design-only, unprivileged, no filesystem writes, no bootloader access.
Run: python3 agent/nexus_recovery_sim.py --self-test
"""
from __future__ import annotations

import argparse
import json
import unittest
from dataclasses import dataclass
from enum import Enum


class Phase(str, Enum):
    IDLE = "idle"
    FETCHED = "fetched"
    VERIFIED = "verified"
    STAGED = "staged"
    PENDING_BOOT = "pending_boot"
    BOOTING = "booting"
    HEALTHY = "healthy"


@dataclass
class Recovery:
    good: str = "A"
    candidate: str | None = None
    phase: Phase = Phase.IDLE
    attempts_left: int = 0
    max_attempts: int = 3

    def __post_init__(self) -> None:
        if self.good not in ("A", "B"):
            raise ValueError("invalid good slot")
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")

    def require(self, expected: Phase) -> None:
        if self.phase != expected:
            raise ValueError(f"expected {expected.value}, got {self.phase.value}")

    def fetch(self) -> None:
        self.require(Phase.IDLE)
        self.candidate = "B" if self.good == "A" else "A"
        self.phase = Phase.FETCHED

    def verify(self, signature_ok: bool, digest_ok: bool) -> None:
        self.require(Phase.FETCHED)
        if not (signature_ok and digest_ok):
            self.abort()
            return
        self.phase = Phase.VERIFIED

    def stage(self) -> None:
        self.require(Phase.VERIFIED)
        self.phase = Phase.STAGED

    def activate(self) -> None:
        self.require(Phase.STAGED)
        self.attempts_left = self.max_attempts
        self.phase = Phase.PENDING_BOOT

    def boot(self) -> str:
        self.require(Phase.PENDING_BOOT)
        if self.attempts_left <= 0:
            raise ValueError("no attempts remaining")
        self.attempts_left -= 1
        self.phase = Phase.BOOTING
        assert self.candidate is not None
        return self.candidate

    def health(self, passed: bool) -> None:
        self.require(Phase.BOOTING)
        if passed:
            assert self.candidate is not None
            self.good = self.candidate
            self.candidate = None
            self.attempts_left = 0
            self.phase = Phase.HEALTHY
        elif self.attempts_left:
            self.phase = Phase.PENDING_BOOT
        else:
            self.abort()

    def abort(self) -> None:
        self.candidate = None
        self.attempts_left = 0
        self.phase = Phase.IDLE

    def reset(self) -> None:
        self.require(Phase.HEALTHY)
        self.phase = Phase.IDLE

    def snapshot(self) -> dict:
        return {
            "good": self.good, "candidate": self.candidate,
            "phase": self.phase.value, "attempts_left": self.attempts_left,
        }


class RecoveryTests(unittest.TestCase):
    def test_success(self):
        r = Recovery()
        r.fetch(); r.verify(True, True); r.stage(); r.activate()
        self.assertEqual(r.boot(), "B")
        r.health(True)
        self.assertEqual((r.good, r.candidate, r.phase), ("B", None, Phase.HEALTHY))

    def test_bad_signature_preserves_good(self):
        r = Recovery()
        r.fetch(); r.verify(False, True)
        self.assertEqual((r.good, r.candidate, r.phase), ("A", None, Phase.IDLE))

    def test_bad_digest_preserves_good(self):
        r = Recovery()
        r.fetch(); r.verify(True, False)
        self.assertEqual((r.good, r.candidate, r.phase), ("A", None, Phase.IDLE))

    def test_repeated_failed_boots_rollback(self):
        r = Recovery(max_attempts=2)
        r.fetch(); r.verify(True, True); r.stage(); r.activate()
        for _ in range(2):
            self.assertEqual(r.boot(), "B")
            r.health(False)
        self.assertEqual((r.good, r.candidate, r.phase), ("A", None, Phase.IDLE))

    def test_cannot_activate_unverified_payload(self):
        r = Recovery()
        r.fetch()
        with self.assertRaises(ValueError):
            r.activate()
        self.assertEqual(r.good, "A")

    def test_no_early_confirmation(self):
        r = Recovery()
        r.fetch(); r.verify(True, True); r.stage(); r.activate()
        with self.assertRaises(ValueError):
            r.health(True)
        self.assertEqual(r.good, "A")

    def test_next_update_targets_other_slot(self):
        r = Recovery()
        r.fetch(); r.verify(True, True); r.stage(); r.activate()
        r.boot(); r.health(True); r.reset(); r.fetch()
        self.assertEqual((r.good, r.candidate), ("B", "A"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        unittest.main(argv=["nexus_recovery_sim.py"], exit=False)
    else:
        r = Recovery()
        r.fetch(); r.verify(True, True); r.stage(); r.activate()
        r.boot(); r.health(True)
        print(json.dumps(r.snapshot(), indent=2))
