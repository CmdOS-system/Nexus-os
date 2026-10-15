"""Serialized Recovery G2 controller prototype; not a bootloader.

Image authenticity and durable staging are caller responsibilities.
All cooperating writers must use this controller/lock protocol.
"""
from .boot_state import stage, select_boot, confirm, rollback
from .store import RedundantStore
from .locking import recovery_lock

class RecoveryController:
    def __init__(self, directory):
        self.store = RedundantStore(directory)

    def stage_verified(self, slot, *, authenticated, image_durable, attempts=3):
        if authenticated is not True or image_durable is not True:
            raise ValueError("authenticated durable image required")
        with recovery_lock(self.store.directory):
            state = stage(self.store.load(), slot, attempts)
            self.store.save(state)
            return state

    def prepare_boot(self):
        with recovery_lock(self.store.directory):
            current = self.store.load()
            selected, state = select_boot(current)
            if state != current:
                self.store.save(state)
            return selected

    def confirm_health(self, booted_slot, *, healthy):
        with recovery_lock(self.store.directory):
            state = confirm(self.store.load(), booted_slot, healthy)
            self.store.save(state)
            return state

    def cancel_update(self):
        with recovery_lock(self.store.directory):
            state = rollback(self.store.load())
            self.store.save(state)
            return state
