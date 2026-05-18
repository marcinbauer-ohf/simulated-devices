"""Alarm control panel platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_ALARM_PANEL
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity

_STATE_MAP = {
    "disarmed": AlarmControlPanelState.DISARMED,
    "armed_home": AlarmControlPanelState.ARMED_HOME,
    "armed_away": AlarmControlPanelState.ARMED_AWAY,
    "armed_night": AlarmControlPanelState.ARMED_NIGHT,
    "triggered": AlarmControlPanelState.TRIGGERED,
    "pending": AlarmControlPanelState.PENDING,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated alarm control panel entities."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    if coordinator.device_type != DEVICE_TYPE_ALARM_PANEL:
        return
    async_add_entities([SimulatedAlarmPanelEntity(coordinator)])


class SimulatedAlarmPanelEntity(SimulatedEntity, AlarmControlPanelEntity):
    """Simulated alarm control panel."""

    _attr_icon = "mdi:shield-home"
    _attr_code_arm_required = False
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_HOME
        | AlarmControlPanelEntityFeature.ARM_AWAY
        | AlarmControlPanelEntityFeature.ARM_NIGHT
        | AlarmControlPanelEntityFeature.TRIGGER
    )

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "alarm", "Alarm")

    @property
    def alarm_state(self) -> AlarmControlPanelState:
        return _STATE_MAP.get(
            self.coordinator.data.get("alarm_state", "disarmed"),
            AlarmControlPanelState.DISARMED,
        )

    async def async_alarm_disarm(self, code=None) -> None:
        self.coordinator.set_state(alarm_state="disarmed")

    async def async_alarm_arm_home(self, code=None) -> None:
        self.coordinator.set_state(alarm_state="armed_home")

    async def async_alarm_arm_away(self, code=None) -> None:
        self.coordinator.set_state(alarm_state="armed_away")

    async def async_alarm_arm_night(self, code=None) -> None:
        self.coordinator.set_state(alarm_state="armed_night")

    async def async_alarm_trigger(self, code=None) -> None:
        self.coordinator.set_state(alarm_state="triggered")
