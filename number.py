"""Number platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_HOME_HUB
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated number entities."""
    async_add_entities(
        SimulatedNumberEntity(c) for c in coordinators_for(entry, DEVICE_TYPE_HOME_HUB)
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
