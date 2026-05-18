"""Lock platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.lock import LockEntity, LockEntityFeature, LockState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_SMART_LOCK
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity

_LOCK_STATE_MAP = {
    "locked": LockState.LOCKED,
    "unlocked": LockState.UNLOCKED,
    "locking": LockState.LOCKING,
    "unlocking": LockState.UNLOCKING,
    "jammed": LockState.JAMMED,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated lock entities."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    if coordinator.device_type != DEVICE_TYPE_SMART_LOCK:
        return
    async_add_entities([SimulatedLockEntity(coordinator)])


class SimulatedLockEntity(SimulatedEntity, LockEntity):
    """Simulated smart lock."""

    _attr_icon = "mdi:lock"
    _attr_supported_features = LockEntityFeature.OPEN

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "lock", "Lock")

    @property
    def is_locked(self) -> bool:
        return self.coordinator.data.get("lock_state") == "locked"

    @property
    def is_locking(self) -> bool:
        return self.coordinator.data.get("lock_state") == "locking"

    @property
    def is_unlocking(self) -> bool:
        return self.coordinator.data.get("lock_state") == "unlocking"

    @property
    def is_jammed(self) -> bool:
        return self.coordinator.data.get("lock_state") == "jammed"

    async def async_lock(self, **kwargs) -> None:
        self.coordinator.set_state(lock_state="locking")

    async def async_unlock(self, **kwargs) -> None:
        self.coordinator.set_state(lock_state="unlocking")

    async def async_open(self, **kwargs) -> None:
        self.coordinator.set_state(lock_state="unlocked", door_contact=True)
