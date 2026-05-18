"""Valve platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.valve import ValveEntity, ValveEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_SMART_VALVE
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated valve entities."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    if coordinator.device_type != DEVICE_TYPE_SMART_VALVE:
        return
    async_add_entities([SimulatedValveEntity(coordinator)])


class SimulatedValveEntity(SimulatedEntity, ValveEntity):
    """Simulated smart valve."""

    _attr_icon = "mdi:valve"
    _attr_supported_features = ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE
    _attr_reports_position = False

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "valve", "Valve")

    @property
    def is_closed(self) -> bool:
        return not bool(self.coordinator.data.get("is_open", False))

    async def async_open_valve(self, **kwargs) -> None:
        self.coordinator.set_state(is_open=True)

    async def async_close_valve(self, **kwargs) -> None:
        self.coordinator.set_state(is_open=False, flow_rate_lpm=0.0)
