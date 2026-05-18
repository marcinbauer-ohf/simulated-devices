"""Climate platform for simulated devices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_THERMOSTAT
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity

_HVAC_MODE_MAP = {
    "off": HVACMode.OFF,
    "heat": HVACMode.HEAT,
    "cool": HVACMode.COOL,
    "heat_cool": HVACMode.HEAT_COOL,
}

_HVAC_ACTION_MAP = {
    "off": HVACAction.OFF,
    "idle": HVACAction.IDLE,
    "heating": HVACAction.HEATING,
    "cooling": HVACAction.COOLING,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated climate entities."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    if coordinator.device_type != DEVICE_TYPE_THERMOSTAT:
        return
    async_add_entities([SimulatedThermostatEntity(coordinator)])


class SimulatedThermostatEntity(SimulatedEntity, ClimateEntity):
    """Simulated thermostat with full feature support."""

    _attr_icon = "mdi:thermostat"
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.HEAT_COOL]
    _attr_preset_modes = ["home", "away", "sleep", "eco"]
    _attr_fan_modes = ["auto", "low", "medium", "high"]
    _attr_swing_modes = ["off", "vertical", "horizontal", "both"]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 10.0
    _attr_max_temp = 30.0
    _attr_target_temperature_step = 0.5

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "climate", "Thermostat")

    @property
    def hvac_mode(self) -> HVACMode:
        return _HVAC_MODE_MAP.get(self.coordinator.data.get("hvac_mode", "heat"), HVACMode.HEAT)

    @property
    def hvac_action(self) -> HVACAction:
        return _HVAC_ACTION_MAP.get(self.coordinator.data.get("hvac_action", "idle"), HVACAction.IDLE)

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data.get("current_temp")

    @property
    def target_temperature(self) -> float | None:
        return self.coordinator.data.get("target_temp")

    @property
    def current_humidity(self) -> float | None:
        return self.coordinator.data.get("current_humidity")

    @property
    def preset_mode(self) -> str | None:
        return self.coordinator.data.get("preset_mode")

    @property
    def fan_mode(self) -> str | None:
        return self.coordinator.data.get("fan_mode", "auto")

    @property
    def swing_mode(self) -> str | None:
        return self.coordinator.data.get("swing_mode", "off")

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if temp := kwargs.get("temperature"):
            self.coordinator.set_state(target_temp=float(temp))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        mode_str = {v: k for k, v in _HVAC_MODE_MAP.items()}.get(hvac_mode, "heat")
        self.coordinator.set_state(hvac_mode=mode_str)

    async def async_turn_on(self) -> None:
        self.coordinator.set_state(hvac_mode="heat")

    async def async_turn_off(self) -> None:
        self.coordinator.set_state(hvac_mode="off")

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        self.coordinator.set_state(preset_mode=preset_mode)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        self.coordinator.set_state(fan_mode=fan_mode)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        self.coordinator.set_state(swing_mode=swing_mode)
