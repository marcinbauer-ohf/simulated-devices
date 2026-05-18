"""Sensor platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfVolume,
)

_UNIT_LUX = "lx"
_UNIT_UGM3 = "µg/m³"
_UNIT_PPM = "ppm"
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_TYPE_AIR_QUALITY,
    DEVICE_TYPE_BUTTON_DEVICE,
    DEVICE_TYPE_DOOR_WINDOW_SENSOR,
    DEVICE_TYPE_DOORBELL,
    DEVICE_TYPE_ENERGY_METER,
    DEVICE_TYPE_EV_CHARGER,
    DEVICE_TYPE_GARAGE_DOOR,
    DEVICE_TYPE_HUMIDIFIER,
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
)
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity

# ---------------------------------------------------------------------------
# Shared reusable descriptors
# ---------------------------------------------------------------------------

_BATTERY_SENSOR = SensorEntityDescription(
    key="battery",
    name="Battery",
    native_unit_of_measurement=PERCENTAGE,
    device_class=SensorDeviceClass.BATTERY,
    state_class=SensorStateClass.MEASUREMENT,
)

_TEMPERATURE_C = SensorEntityDescription(
    key="temperature_c",
    name="Temperature",
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
)

_HUMIDITY_PCT = SensorEntityDescription(
    key="humidity_pct",
    name="Humidity",
    native_unit_of_measurement=PERCENTAGE,
    device_class=SensorDeviceClass.HUMIDITY,
    state_class=SensorStateClass.MEASUREMENT,
)

# ---------------------------------------------------------------------------
# Per-device sensor tuples
# ---------------------------------------------------------------------------

_LIGHT_SENSORS: tuple[SensorEntityDescription, ...] = (_BATTERY_SENSOR,)

_PLUG_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="power_w",
        name="Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="energy_kwh",
        name="Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    _BATTERY_SENSOR,
)

_WEATHER_SENSORS: tuple[SensorEntityDescription, ...] = (
    _TEMPERATURE_C,
    _HUMIDITY_PCT,
    _BATTERY_SENSOR,
)

_GARAGE_SENSORS: tuple[SensorEntityDescription, ...] = (_BATTERY_SENSOR,)

_THERMOSTAT_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="current_temp",
        name="Current Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="current_humidity",
        name="Current Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

_HUMIDIFIER_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="current_humidity",
        name="Current Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="water_level_pct",
        name="Water Level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

_SMART_LOCK_SENSORS: tuple[SensorEntityDescription, ...] = (_BATTERY_SENSOR,)

_MOTION_SENSOR_SENSORS: tuple[SensorEntityDescription, ...] = (
    _BATTERY_SENSOR,
    SensorEntityDescription(
        key="illuminance_lx",
        name="Illuminance",
        native_unit_of_measurement=_UNIT_LUX,
        device_class=SensorDeviceClass.ILLUMINANCE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

_DOOR_WINDOW_SENSORS: tuple[SensorEntityDescription, ...] = (
    _BATTERY_SENSOR,
    SensorEntityDescription(
        key="temperature_c",
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

_SMOKE_CO_SENSORS: tuple[SensorEntityDescription, ...] = (
    _BATTERY_SENSOR,
    SensorEntityDescription(
        key="co_ppm",
        name="CO Concentration",
        native_unit_of_measurement=_UNIT_PPM,
        device_class=SensorDeviceClass.CO,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

_ROBOT_VACUUM_SENSORS: tuple[SensorEntityDescription, ...] = (
    _BATTERY_SENSOR,
    SensorEntityDescription(
        key="cleaned_area_m2",
        name="Cleaned Area",
        native_unit_of_measurement="m²",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
)

_AIR_QUALITY_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="pm25_ugm3",
        name="PM2.5",
        native_unit_of_measurement=_UNIT_UGM3,
        device_class=SensorDeviceClass.PM25,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="pm10_ugm3",
        name="PM10",
        native_unit_of_measurement=_UNIT_UGM3,
        device_class=SensorDeviceClass.PM10,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="co2_ppm",
        name="CO2",
        native_unit_of_measurement=_UNIT_PPM,
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="voc_index",
        name="VOC Index",
        native_unit_of_measurement="index",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="aqi",
        name="Air Quality Index",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="temperature_c",
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="humidity_pct",
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

_SMART_VALVE_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="flow_rate_lpm",
        name="Flow Rate",
        native_unit_of_measurement="L/min",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="volume_l",
        name="Total Volume",
        native_unit_of_measurement=UnitOfVolume.LITERS,
        device_class=SensorDeviceClass.WATER,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
)

_WATER_LEAK_SENSORS: tuple[SensorEntityDescription, ...] = (
    _BATTERY_SENSOR,
    SensorEntityDescription(
        key="temperature_c",
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

_ENERGY_METER_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="power_w",
        name="Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="energy_kwh",
        name="Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="voltage_v",
        name="Voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="current_a",
        name="Current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="power_factor",
        name="Power Factor",
        device_class=SensorDeviceClass.POWER_FACTOR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

_EV_CHARGER_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="power_kw",
        name="Charging Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="energy_kwh",
        name="Session Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="vehicle_soc_pct",
        name="Vehicle Battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

_SOLAR_PANEL_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="current_power_w",
        name="Current Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="daily_energy_kwh",
        name="Daily Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="total_energy_kwh",
        name="Total Energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="panel_temp_c",
        name="Panel Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

_SMART_FAN_SENSORS: tuple[SensorEntityDescription, ...] = ()
_SMART_BLIND_SENSORS: tuple[SensorEntityDescription, ...] = (_BATTERY_SENSOR,)
_DOORBELL_SENSORS: tuple[SensorEntityDescription, ...] = (_BATTERY_SENSOR,)
_SIREN_SENSORS: tuple[SensorEntityDescription, ...] = (_BATTERY_SENSOR,)
_BUTTON_DEVICE_SENSORS: tuple[SensorEntityDescription, ...] = (_BATTERY_SENSOR,)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_SENSORS_BY_DEVICE_TYPE: dict[str, tuple[SensorEntityDescription, ...]] = {
    DEVICE_TYPE_SMART_LIGHT: _LIGHT_SENSORS,
    DEVICE_TYPE_SMART_PLUG: _PLUG_SENSORS,
    DEVICE_TYPE_WEATHER_STATION: _WEATHER_SENSORS,
    DEVICE_TYPE_GARAGE_DOOR: _GARAGE_SENSORS,
    DEVICE_TYPE_THERMOSTAT: _THERMOSTAT_SENSORS,
    DEVICE_TYPE_HUMIDIFIER: _HUMIDIFIER_SENSORS,
    DEVICE_TYPE_SMART_LOCK: _SMART_LOCK_SENSORS,
    DEVICE_TYPE_MOTION_SENSOR: _MOTION_SENSOR_SENSORS,
    DEVICE_TYPE_DOOR_WINDOW_SENSOR: _DOOR_WINDOW_SENSORS,
    DEVICE_TYPE_SMOKE_CO_DETECTOR: _SMOKE_CO_SENSORS,
    DEVICE_TYPE_ROBOT_VACUUM: _ROBOT_VACUUM_SENSORS,
    DEVICE_TYPE_AIR_QUALITY: _AIR_QUALITY_SENSORS,
    DEVICE_TYPE_SMART_VALVE: _SMART_VALVE_SENSORS,
    DEVICE_TYPE_WATER_LEAK: _WATER_LEAK_SENSORS,
    DEVICE_TYPE_ENERGY_METER: _ENERGY_METER_SENSORS,
    DEVICE_TYPE_EV_CHARGER: _EV_CHARGER_SENSORS,
    DEVICE_TYPE_SOLAR_PANEL: _SOLAR_PANEL_SENSORS,
    DEVICE_TYPE_SMART_FAN: _SMART_FAN_SENSORS,
    DEVICE_TYPE_SMART_BLIND: _SMART_BLIND_SENSORS,
    DEVICE_TYPE_DOORBELL: _DOORBELL_SENSORS,
    DEVICE_TYPE_SIREN: _SIREN_SENSORS,
    DEVICE_TYPE_BUTTON_DEVICE: _BUTTON_DEVICE_SENSORS,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated sensors."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    descriptions = _SENSORS_BY_DEVICE_TYPE.get(coordinator.device_type, ())
    async_add_entities(
        [SimulatedValueSensor(coordinator, desc) for desc in descriptions]
    )


class SimulatedValueSensor(SimulatedEntity, SensorEntity):
    """A value sensor backed by coordinator data."""

    def __init__(
        self,
        coordinator: SimulatedDeviceCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(
            coordinator,
            description.key,
            description.name or description.key,
        )
        self.entity_description = description

    @property
    def native_value(self):
        return self.coordinator.data.get(self.entity_description.key)
