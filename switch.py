"""Switch platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .child_devices import (
    OUTLETS,
    RIG_DIAGNOSTIC,
    RIG_CHILDREN,
    ChildSpec,
)
from .const import (
    DEVICE_TYPE_CHILD_TEST_RIG,
    DEVICE_TYPE_DUAL_LENS_CAMERA,
    DEVICE_TYPE_EV_CHARGER,
    DEVICE_TYPE_POWER_STRIP,
    DEVICE_TYPE_SMART_PLUG,
)
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated switch entities."""
    async_add_entities(
        [SimulatedPlugSwitchEntity(c) for c in coordinators_for(entry, DEVICE_TYPE_SMART_PLUG)]
        + [SimulatedEVChargerSwitchEntity(c) for c in coordinators_for(entry, DEVICE_TYPE_EV_CHARGER)]
        + [
            SimulatedChildSwitchEntity(c, outlet)
            for c in coordinators_for(entry, DEVICE_TYPE_POWER_STRIP)
            for outlet in OUTLETS
        ]
        + [
            SimulatedPrivacySwitchEntity(c)
            for c in coordinators_for(entry, DEVICE_TYPE_DUAL_LENS_CAMERA)
        ]
        + [
            SimulatedChildSwitchEntity(c, child)
            for c in coordinators_for(entry, DEVICE_TYPE_CHILD_TEST_RIG)
            for child in RIG_CHILDREN
            # The diagnostics-only child must stay out of the Controls card.
            if child is not RIG_DIAGNOSTIC
        ]
    )


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


class SimulatedChildSwitchEntity(SimulatedEntity, SwitchEntity):
    """On/off switch living on a child device (a power strip outlet)."""

    _attr_icon = "mdi:power-socket-eu"

    def __init__(
        self, coordinator: SimulatedDeviceCoordinator, child: ChildSpec
    ) -> None:
        super().__init__(coordinator, "switch", "Switch", child=child)
        self._key = child.state_key("is_on")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get(self._key, False))

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.set_state(**{self._key: True})

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.set_state(**{self._key: False})


class SimulatedPrivacySwitchEntity(SimulatedEntity, SwitchEntity):
    """Privacy mode on the dual-lens camera parent — blinds both lenses."""

    _attr_icon = "mdi:eye-off"

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "privacy_mode", "Privacy mode")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("privacy_mode", False))

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.set_state(privacy_mode=True)

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.set_state(privacy_mode=False)
