"""Time platform for simulated devices."""

from __future__ import annotations

from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_HOME_HUB
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated time entities."""
    async_add_entities(
        SimulatedTimeEntity(c) for c in coordinators_for(entry, DEVICE_TYPE_HOME_HUB)
    )


class SimulatedTimeEntity(SimulatedEntity, TimeEntity):
    """Simulated time-of-day field, e.g. a daily schedule."""

    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "schedule_time", "Schedule Time")

    @property
    def native_value(self) -> time | None:
        raw = self.coordinator.data.get("time_value")
        return time.fromisoformat(raw) if raw else None

    async def async_set_value(self, value: time) -> None:
        self.coordinator.set_state(time_value=value.isoformat())
