"""High-level transactional facade for Recovery G2; NOT a bootloader.

Caller must authenticate and durably stage the inactive image before stage_verified().
Caller must persist returned boot decision before transferring control to bootloader.
"""
from .boot_state import stage, select_boot, confirm, rollback
from .store import RedundantStore

class RecoveryController:
    def __init__(self, directory):
        self.store = RedundantStore(directory)

    def stage_verified(self, slot, *, authenticated, image_durable, attempts=3):
        if authenticated is not True or image_durable is not True:
            raise ValueError("authenticated durable image required")
        state = stage(self.store.load(), slot, attempts)
        self.store.save(state)
        return state

    def prepare_boot(self):
        selected, state = select_boot(self.store.load())
        current = self.store.load()
        if state != current:
            self.store.save(state)
        return selected

    def confirm_health(self, booted_slot, *, healthy):
        state = confirm(self.store.load(), booted_slot, healthy)
        self.store.save(state)
        return state

    def cancel_update(self):
        state = rollback(self.store.load())
        self.store.save(state)
        return state
