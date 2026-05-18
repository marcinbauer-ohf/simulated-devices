"""Siren platform for simulated devices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.siren import SirenEntity, SirenEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_SIREN
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated siren entities."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    if coordinator.device_type != DEVICE_TYPE_SIREN:
        return
    async_add_entities([SimulatedSirenEntity(coordinator)])


class SimulatedSirenEntity(SimulatedEntity, SirenEntity):
    """Simulated siren."""

    _attr_icon = "mdi:alarm-bell"
    _attr_available_tones = ["default", "fire", "burglar", "medical"]
    _attr_supported_features = (
        SirenEntityFeature.TURN_ON
        | SirenEntityFeature.TURN_OFF
        | SirenEntityFeature.TONES
        | SirenEntityFeature.VOLUME_SET
        | SirenEntityFeature.DURATION
    )

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "siren", "Siren")

    @property
    def is_on(self) -> bool | None:
        return bool(self.coordinator.data.get("is_on", False))

    async def async_turn_on(self, **kwargs: Any) -> None:
        updates: dict = {"is_on": True}
        if tone := kwargs.get("tone"):
            updates["tone"] = tone
        if volume := kwargs.get("volume_level"):
            updates["volume_level"] = volume
        self.coordinator.set_state(**updates)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.set_state(is_on=False)
