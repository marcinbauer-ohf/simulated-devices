"""Binary sensor platform for simulated devices."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_TYPE_ALARM_PANEL,
    DEVICE_TYPE_AIR_QUALITY,
    DEVICE_TYPE_DOOR_WINDOW_SENSOR,
    DEVICE_TYPE_DOORBELL,
    DEVICE_TYPE_ENERGY_METER,
    DEVICE_TYPE_EV_CHARGER,
    DEVICE_TYPE_GARAGE_DOOR,
    DEVICE_TYPE_HUMIDIFIER,
    DEVICE_TYPE_MEDIA_PLAYER,
    DEVICE_TYPE_MOTION_SENSOR,
    DEVICE_TYPE_ROBOT_VACUUM,
    DEVICE_TYPE_SIREN,
    DEVICE_TYPE_SMART_BLIND,
    DEVICE_TYPE_SMART_FAN,
    DEVICE_TYPE_SMART_LIGHT,
    DEVICE_TYPE_SMART_LOCK,
    DEVICE_TYPE_SMART_PLUG,
    DEVICE_TYPE_SMART_VALVE,
    DEVICE_TYPE_SMOKE_CO_DETECTOR,
    DEVICE_TYPE_SOLAR_PANEL,
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_WATER_LEAK,
    DEVICE_TYPE_WEATHER_STATION,
    DEVICE_TYPE_BUTTON_DEVICE,
)
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity


@dataclass
class SimulatedBinarySensorDescription:
    """Description for a data-driven binary sensor."""

    key: str
    name: str
    device_class: BinarySensorDeviceClass | None = None
    entity_category: EntityCategory | None = None
    inverted: bool = False


# Devices that have a persistent connectivity binary sensor
_DEVICES_WITH_CONNECTIVITY = {
    DEVICE_TYPE_SMART_LIGHT,
    DEVICE_TYPE_SMART_PLUG,
    DEVICE_TYPE_WEATHER_STATION,
    DEVICE_TYPE_GARAGE_DOOR,
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_HUMIDIFIER,
    DEVICE_TYPE_SMART_LOCK,
    DEVICE_TYPE_MEDIA_PLAYER,
    DEVICE_TYPE_ROBOT_VACUUM,
    DEVICE_TYPE_AIR_QUALITY,
    DEVICE_TYPE_SMART_VALVE,
    DEVICE_TYPE_ALARM_PANEL,
    DEVICE_TYPE_SIREN,
    DEVICE_TYPE_ENERGY_METER,
    DEVICE_TYPE_EV_CHARGER,
    DEVICE_TYPE_SOLAR_PANEL,
    DEVICE_TYPE_SMART_BLIND,
    DEVICE_TYPE_DOORBELL,
    DEVICE_TYPE_SMART_FAN,
    DEVICE_TYPE_BUTTON_DEVICE,
}

_BINARY_SENSORS_BY_DEVICE_TYPE: dict[str, tuple[SimulatedBinarySensorDescription, ...]] = {
    DEVICE_TYPE_GARAGE_DOOR: (
        SimulatedBinarySensorDescription(
            key="obstruction",
            name="Obstruction",
            device_class=BinarySensorDeviceClass.PROBLEM,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    ),
    DEVICE_TYPE_SMART_LOCK: (
        SimulatedBinarySensorDescription(
            key="door_contact",
            name="Door",
            device_class=BinarySensorDeviceClass.DOOR,
        ),
    ),
    DEVICE_TYPE_MOTION_SENSOR: (
        SimulatedBinarySensorDescription(
            key="motion",
            name="Motion",
            device_class=BinarySensorDeviceClass.MOTION,
        ),
        SimulatedBinarySensorDescription(
            key="tamper",
            name="Tamper",
            device_class=BinarySensorDeviceClass.TAMPER,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    ),
    DEVICE_TYPE_DOOR_WINDOW_SENSOR: (
        SimulatedBinarySensorDescription(
            key="contact",
            name="Contact",
            device_class=BinarySensorDeviceClass.DOOR,
        ),
        SimulatedBinarySensorDescription(
            key="tamper",
            name="Tamper",
            device_class=BinarySensorDeviceClass.TAMPER,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    ),
    DEVICE_TYPE_SMOKE_CO_DETECTOR: (
        SimulatedBinarySensorDescription(
            key="smoke",
            name="Smoke",
            device_class=BinarySensorDeviceClass.SMOKE,
        ),
        SimulatedBinarySensorDescription(
            key="carbon_monoxide",
            name="Carbon Monoxide",
            device_class=BinarySensorDeviceClass.CO,
        ),
        SimulatedBinarySensorDescription(
            key="battery_low",
            name="Battery Low",
            device_class=BinarySensorDeviceClass.BATTERY,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    ),
    DEVICE_TYPE_SMART_VALVE: (
        SimulatedBinarySensorDescription(
            key="leak_detected",
            name="Leak",
            device_class=BinarySensorDeviceClass.MOISTURE,
        ),
    ),
    DEVICE_TYPE_WATER_LEAK: (
        SimulatedBinarySensorDescription(
            key="moisture",
            name="Moisture",
            device_class=BinarySensorDeviceClass.MOISTURE,
        ),
        SimulatedBinarySensorDescription(
            key="battery_low",
            name="Battery Low",
            device_class=BinarySensorDeviceClass.BATTERY,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    ),
    DEVICE_TYPE_ENERGY_METER: (
        SimulatedBinarySensorDescription(
            key="overload",
            name="Overload",
            device_class=BinarySensorDeviceClass.PROBLEM,
        ),
    ),
    DEVICE_TYPE_EV_CHARGER: (
        SimulatedBinarySensorDescription(
            key="vehicle_connected",
            name="Vehicle Connected",
            device_class=BinarySensorDeviceClass.PLUG,
        ),
    ),
    DEVICE_TYPE_SOLAR_PANEL: (
        SimulatedBinarySensorDescription(
            key="fault",
            name="Fault",
            device_class=BinarySensorDeviceClass.PROBLEM,
        ),
    ),
    DEVICE_TYPE_DOORBELL: (
        SimulatedBinarySensorDescription(
            key="motion",
            name="Motion",
            device_class=BinarySensorDeviceClass.MOTION,
        ),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated binary sensors."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []

    if coordinator.device_type in _DEVICES_WITH_CONNECTIVITY:
        entities.append(SimulatedConnectivityBinarySensor(coordinator))

    for desc in _BINARY_SENSORS_BY_DEVICE_TYPE.get(coordinator.device_type, ()):
        entities.append(SimulatedBinarySensor(coordinator, desc))

    async_add_entities(entities)


class SimulatedConnectivityBinarySensor(SimulatedEntity, BinarySensorEntity):
    """Connectivity sensor — always available even when device is offline."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "connected", "Connected")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("connected", True))

    @property
    def available(self) -> bool:
        return True


class SimulatedBinarySensor(SimulatedEntity, BinarySensorEntity):
    """Generic data-driven binary sensor."""

    def __init__(
        self,
        coordinator: SimulatedDeviceCoordinator,
        description: SimulatedBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key, description.name)
        self._attr_device_class = description.device_class
        self._attr_entity_category = description.entity_category
        self._description = description

    @property
    def is_on(self) -> bool:
        val = bool(self.coordinator.data.get(self._description.key, False))
        return not val if self._description.inverted else val
