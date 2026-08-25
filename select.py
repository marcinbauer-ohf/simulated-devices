"""Select platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_HOME_HUB
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity

_OPTIONS = ["Comfort", "Eco", "Boost", "Away", "Sleep"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated select entities."""
    async_add_entities(
        SimulatedSelectEntity(c) for c in coordinators_for(entry, DEVICE_TYPE_HOME_HUB)
    )


class SimulatedSelectEntity(SimulatedEntity, SelectEntity):
    """Simulated mode selector."""

    _attr_icon = "mdi:format-list-bulleted"
    _attr_options = _OPTIONS

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "mode", "Mode")

    @property
    def current_option(self) -> str | None:
        return self.coordinator.data.get("select_option")

    async def async_select_option(self, option: str) -> None:
        self.coordinator.set_state(select_option=option)
