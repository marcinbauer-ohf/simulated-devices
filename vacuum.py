"""Vacuum platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_ROBOT_VACUUM
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity

_STATUS_MAP = {
    "cleaning": VacuumActivity.CLEANING,
    "docked": VacuumActivity.DOCKED,
    "returning": VacuumActivity.RETURNING,
    "paused": VacuumActivity.PAUSED,
    "error": VacuumActivity.ERROR,
    "idle": VacuumActivity.IDLE,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated vacuum entities."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    if coordinator.device_type != DEVICE_TYPE_ROBOT_VACUUM:
        return
    async_add_entities([SimulatedRobotVacuumEntity(coordinator)])


class SimulatedRobotVacuumEntity(SimulatedEntity, StateVacuumEntity):
    """Simulated robot vacuum."""

    _attr_icon = "mdi:robot-vacuum"
    _attr_fan_speed_list = ["quiet", "normal", "turbo", "max"]
    _attr_supported_features = (
        VacuumEntityFeature.START
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.PAUSE
    )

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "vacuum", "Vacuum")

    @property
    def activity(self) -> VacuumActivity:
        return _STATUS_MAP.get(
            self.coordinator.data.get("status", "docked"), VacuumActivity.DOCKED
        )

    @property
    def battery_level(self) -> int | None:
        batt = self.coordinator.data.get("battery")
        return int(batt) if batt is not None else None

    @property
    def fan_speed(self) -> str | None:
        return self.coordinator.data.get("fan_speed")

    async def async_start(self) -> None:
        self.coordinator.set_state(status="cleaning")

    async def async_stop(self, **kwargs) -> None:
        self.coordinator.set_state(status="idle")

    async def async_pause(self) -> None:
        self.coordinator.set_state(status="paused")

    async def async_return_to_base(self, **kwargs) -> None:
        self.coordinator.set_state(status="returning")

    async def async_set_fan_speed(self, fan_speed: str, **kwargs) -> None:
        self.coordinator.set_state(fan_speed=fan_speed)
