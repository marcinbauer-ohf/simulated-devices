"""Text platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
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
    """Set up simulated text entities."""
    async_add_entities(
        SimulatedTextEntity(c) for c in coordinators_for(entry, DEVICE_TYPE_HOME_HUB)
    )


class SimulatedTextEntity(SimulatedEntity, TextEntity):
    """Simulated free-text field."""

    _attr_icon = "mdi:form-textbox"
    _attr_mode = TextMode.TEXT
    _attr_native_max = 100

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "message", "Message")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("text_value")

    async def async_set_value(self, value: str) -> None:
        self.coordinator.set_state(text_value=value)
