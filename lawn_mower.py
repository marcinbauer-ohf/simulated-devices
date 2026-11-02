"""Lawn mower platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.lawn_mower import (
    LawnMowerActivity,
    LawnMowerEntity,
    LawnMowerEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_LAWN_MOWER
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity

_ACTIVITY_MAP = {
    "mowing": LawnMowerActivity.MOWING,
    "docked": LawnMowerActivity.DOCKED,
    "paused": LawnMowerActivity.PAUSED,
    "returning": LawnMowerActivity.RETURNING,
    "error": LawnMowerActivity.ERROR,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated lawn mower entities."""
    async_add_entities(
        SimulatedLawnMowerEntity(c)
        for c in coordinators_for(entry, DEVICE_TYPE_LAWN_MOWER)
    )


class SimulatedLawnMowerEntity(SimulatedEntity, LawnMowerEntity):
    """Simulated robotic lawn mower."""

    _attr_icon = "mdi:robot-mower"
    _attr_supported_features = (
        LawnMowerEntityFeature.START_MOWING
        | LawnMowerEntityFeature.PAUSE
        | LawnMowerEntityFeature.DOCK
    )

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "lawn_mower", "Mower")

    @property
    def activity(self) -> LawnMowerActivity:
        return _ACTIVITY_MAP.get(
            self.coordinator.data.get("activity", "docked"), LawnMowerActivity.DOCKED
        )

    async def async_start_mowing(self) -> None:
        self.coordinator.set_state(activity="mowing", error=False)

    async def async_pause(self) -> None:
        self.coordinator.set_state(activity="paused")

    async def async_dock(self) -> None:
        self.coordinator.set_state(activity="returning")
