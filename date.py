"""Date platform for simulated devices."""

from __future__ import annotations

from datetime import date

from homeassistant.components.date import DateEntity
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
    """Set up simulated date entities."""
    async_add_entities(
        SimulatedDateEntity(c) for c in coordinators_for(entry, DEVICE_TYPE_HOME_HUB)
    )


class SimulatedDateEntity(SimulatedEntity, DateEntity):
    """Simulated date field, e.g. a service date."""

    _attr_icon = "mdi:calendar"

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "service_date", "Service Date")

    @property
    def native_value(self) -> date | None:
        raw = self.coordinator.data.get("date_value")
        return date.fromisoformat(raw) if raw else None

    async def async_set_value(self, value: date) -> None:
        self.coordinator.set_state(date_value=value.isoformat())
