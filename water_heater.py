"""Water heater platform for simulated devices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_WATER_HEATER
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity

_OPERATION_MODES = ["eco", "performance", "high_demand", "heat_pump", "off"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated water heater entities."""
    async_add_entities(
        SimulatedWaterHeaterEntity(c)
        for c in coordinators_for(entry, DEVICE_TYPE_WATER_HEATER)
    )


class SimulatedWaterHeaterEntity(SimulatedEntity, WaterHeaterEntity):
    """Simulated water heater."""

    _attr_icon = "mdi:water-boiler"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_operation_list = _OPERATION_MODES
    _attr_min_temp = 30.0
    _attr_max_temp = 80.0
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
        | WaterHeaterEntityFeature.AWAY_MODE
        | WaterHeaterEntityFeature.ON_OFF
    )

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "water_heater", "Water Heater")

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data.get("current_temp")

    @property
    def target_temperature(self) -> float | None:
        return self.coordinator.data.get("target_temp")

    @property
    def current_operation(self) -> str | None:
        if not self.coordinator.data.get("is_on", True):
            return "off"
        return self.coordinator.data.get("operation_mode", "eco")

    @property
    def is_away_mode_on(self) -> bool:
        return bool(self.coordinator.data.get("away_mode", False))

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            self.coordinator.set_state(target_temp=float(temperature))

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        if operation_mode == "off":
            self.coordinator.set_state(is_on=False)
        else:
            self.coordinator.set_state(is_on=True, operation_mode=operation_mode)

    async def async_turn_away_mode_on(self) -> None:
        self.coordinator.set_state(away_mode=True)

    async def async_turn_away_mode_off(self) -> None:
        self.coordinator.set_state(away_mode=False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.coordinator.set_state(is_on=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.set_state(is_on=False, heating=False)
