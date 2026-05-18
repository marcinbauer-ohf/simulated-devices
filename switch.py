"""Switch platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_EV_CHARGER, DEVICE_TYPE_SMART_PLUG
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated switch entities."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    if coordinator.device_type == DEVICE_TYPE_SMART_PLUG:
        async_add_entities([SimulatedPlugSwitchEntity(coordinator)])
    elif coordinator.device_type == DEVICE_TYPE_EV_CHARGER:
        async_add_entities([SimulatedEVChargerSwitchEntity(coordinator)])


class SimulatedPlugSwitchEntity(SimulatedEntity, SwitchEntity):
    """Simulated smart plug switch."""

    _attr_icon = "mdi:power-socket-eu"

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "switch", "Switch")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data["is_on"])

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.set_state(is_on=True, power_w=80.0)

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.set_state(is_on=False, power_w=0.0)


class SimulatedEVChargerSwitchEntity(SimulatedEntity, SwitchEntity):
    """Simulated EV charger on/off switch."""

    _attr_icon = "mdi:ev-station"

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "charging", "Charging")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("charging", False))

    async def async_turn_on(self, **kwargs) -> None:
        if self.coordinator.data.get("vehicle_connected"):
            self.coordinator.set_state(charging=True)

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.set_state(charging=False, power_kw=0.0)
