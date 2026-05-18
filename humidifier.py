"""Humidifier platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.humidifier import (
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_HUMIDIFIER
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated humidifier entities."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    if coordinator.device_type != DEVICE_TYPE_HUMIDIFIER:
        return
    async_add_entities([SimulatedHumidifierEntity(coordinator)])


class SimulatedHumidifierEntity(SimulatedEntity, HumidifierEntity):
    """Simulated humidifier."""

    _attr_icon = "mdi:air-humidifier"
    _attr_device_class = HumidifierDeviceClass.HUMIDIFIER
    _attr_available_modes = ["auto", "sleep", "baby"]
    _attr_min_humidity = 30
    _attr_max_humidity = 80
    _attr_supported_features = HumidifierEntityFeature.MODES

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "humidifier", "Humidifier")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("is_on", False))

    @property
    def current_humidity(self) -> float | None:
        return self.coordinator.data.get("current_humidity")

    @property
    def target_humidity(self) -> int | None:
        return self.coordinator.data.get("target_humidity")

    @property
    def mode(self) -> str | None:
        return self.coordinator.data.get("mode")

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.set_state(is_on=True)

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.set_state(is_on=False)

    async def async_set_humidity(self, humidity: int) -> None:
        self.coordinator.set_state(target_humidity=max(30, min(80, humidity)))

    async def async_set_mode(self, mode: str) -> None:
        self.coordinator.set_state(mode=mode)
