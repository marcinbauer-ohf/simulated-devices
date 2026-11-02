"""Number platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .child_devices import RIG_DIAGNOSTIC
from .const import DEVICE_TYPE_CHILD_TEST_RIG, DEVICE_TYPE_HOME_HUB
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated number entities."""
    async_add_entities(
        [SimulatedNumberEntity(c) for c in coordinators_for(entry, DEVICE_TYPE_HOME_HUB)]
        + [
            SimulatedRigConfigNumberEntity(c)
            for c in coordinators_for(entry, DEVICE_TYPE_CHILD_TEST_RIG)
        ]
    )


class SimulatedNumberEntity(SimulatedEntity, NumberEntity):
    """Simulated setpoint."""

    _attr_icon = "mdi:thermometer"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 5.0
    _attr_native_max_value = 35.0
    _attr_native_step = 0.5
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "setpoint", "Setpoint")

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("number_value")

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.set_state(number_value=round(value, 1))


class SimulatedRigConfigNumberEntity(SimulatedEntity, NumberEntity):
    """Config entity on the test rig's diagnostics-only child.

    Together with that child's Fault sensor it gives a child whose entities are
    all diagnostic or config, which must not show up in the parent's Controls
    or Sensors cards.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 5.0
    _attr_native_max_value = 35.0
    _attr_native_step = 0.5
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "setpoint", "Setpoint", child=RIG_DIAGNOSTIC)
        self._key = RIG_DIAGNOSTIC.state_key("setpoint")

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get(self._key)

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.set_state(**{self._key: round(value, 1)})
