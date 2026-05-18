"""Event platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_BUTTON_DEVICE, DEVICE_TYPE_DOORBELL
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated event entities."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    if coordinator.device_type == DEVICE_TYPE_BUTTON_DEVICE:
        async_add_entities([SimulatedButtonEventEntity(coordinator)])
    elif coordinator.device_type == DEVICE_TYPE_DOORBELL:
        async_add_entities([SimulatedDoorbellEventEntity(coordinator)])


class SimulatedButtonEventEntity(SimulatedEntity, EventEntity):
    """Simulated button device — fires press events."""

    _attr_icon = "mdi:gesture-tap-button"
    _attr_event_types = ["single_press", "double_press", "long_press"]

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "button_event", "Button")
        self._last_seen_event_time: str | None = None

    def _handle_coordinator_update(self) -> None:
        event_time = self.coordinator.data.get("last_event_time")
        if event_time and event_time != self._last_seen_event_time:
            self._last_seen_event_time = event_time
            event_type = self.coordinator.data.get("last_event", "single_press")
            self._trigger_event(event_type)
        super()._handle_coordinator_update()


class SimulatedDoorbellEventEntity(SimulatedEntity, EventEntity):
    """Simulated doorbell — fires press events."""

    _attr_icon = "mdi:doorbell"
    _attr_event_types = ["press"]

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "doorbell_event", "Doorbell")
        self._last_seen_press_time: str | None = None

    def _handle_coordinator_update(self) -> None:
        press_time = self.coordinator.data.get("last_press_time")
        if press_time and press_time != self._last_seen_press_time:
            self._last_seen_press_time = press_time
            self._trigger_event("press")
        super()._handle_coordinator_update()
