"""Pure Recovery G2 boot decision logic; no persistent I/O."""
from dataclasses import dataclass, replace
from typing import Literal

Slot = Literal["A", "B"]

@dataclass(frozen=True)
class BootState:
    confirmed: Slot = "A"
    candidate: Slot | None = None
    attempts_left: int = 0
    generation: int = 0

    def __post_init__(self):
        if self.confirmed not in ("A", "B") or self.candidate not in (None, "A", "B"):
            raise ValueError("invalid slot")
        if self.candidate == self.confirmed:
            raise ValueError("candidate must be inactive")
        if self.attempts_left < 0 or self.generation < 0:
            raise ValueError("negative counter")
        if self.candidate is None and self.attempts_left:
            raise ValueError("orphan attempt budget")

def stage(state: BootState, slot: Slot, attempts: int = 3) -> BootState:
    """Caller MUST authenticate, verify, and durably stage the image first."""
    if state.candidate is not None or slot not in ("A", "B") or slot == state.confirmed:
        raise ValueError("unsafe update target")
    if not 1 <= attempts <= 10:
        raise ValueError("invalid attempt budget")
    return replace(state, candidate=slot, attempts_left=attempts,
                   generation=state.generation + 1)

def select_boot(state: BootState) -> tuple[Slot, BootState]:
    """Persist returned state BEFORE boot. Zero budget falls back next boot."""
    if state.candidate is None:
        return state.confirmed, state
    if state.attempts_left == 0:
        return state.confirmed, rollback(state)
    return state.candidate, replace(state, attempts_left=state.attempts_left - 1,
                                    generation=state.generation + 1)

def confirm(state: BootState, booted_slot: Slot, healthy: bool) -> BootState:
    if not healthy or state.candidate != booted_slot:
        raise ValueError("health confirmation required for tentative slot")
    return BootState(confirmed=booted_slot, generation=state.generation + 1)

def rollback(state: BootState) -> BootState:
    return BootState(confirmed=state.confirmed, generation=state.generation + 1)
