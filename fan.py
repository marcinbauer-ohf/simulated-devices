"""Fan platform for simulated devices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_SMART_FAN
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated fan entities."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    if coordinator.device_type != DEVICE_TYPE_SMART_FAN:
        return
    async_add_entities([SimulatedFanEntity(coordinator)])


class SimulatedFanEntity(SimulatedEntity, FanEntity):
    """Simulated smart fan with full feature support."""

    _attr_icon = "mdi:fan"
    _attr_preset_modes = ["normal", "sleep", "turbo"]
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.OSCILLATE
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.DIRECTION
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "fan", "Fan")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("is_on", False))

    @property
    def percentage(self) -> int | None:
        return self.coordinator.data.get("percentage")

    @property
    def oscillating(self) -> bool | None:
        return self.coordinator.data.get("oscillating")

    @property
    def preset_mode(self) -> str | None:
        return self.coordinator.data.get("preset_mode")

    @property
    def current_direction(self) -> str | None:
        return self.coordinator.data.get("direction", "forward")

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any) -> None:
        updates: dict = {"is_on": True}
        if percentage is not None:
            updates["percentage"] = max(1, min(100, percentage))
        if preset_mode is not None:
            updates["preset_mode"] = preset_mode
        self.coordinator.set_state(**updates)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.set_state(is_on=False)

    async def async_set_percentage(self, percentage: int) -> None:
        self.coordinator.set_state(percentage=max(1, min(100, percentage)))

    async def async_oscillate(self, oscillating: bool) -> None:
        self.coordinator.set_state(oscillating=oscillating)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        self.coordinator.set_state(preset_mode=preset_mode)

    async def async_set_direction(self, direction: str) -> None:
        self.coordinator.set_state(direction=direction)
