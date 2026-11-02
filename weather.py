"""Weather platform for simulated devices."""

from __future__ import annotations

import random
from datetime import timedelta

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import (
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DEVICE_TYPE_WEATHER_STATION
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity

_CONDITIONS = [
    "sunny",
    "partlycloudy",
    "cloudy",
    "rainy",
    "pouring",
    "windy",
    "fog",
    "snowy",
    "lightning-rainy",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated weather entities."""
    async_add_entities(
        SimulatedWeatherEntity(c)
        for c in coordinators_for(entry, DEVICE_TYPE_WEATHER_STATION)
    )


class SimulatedWeatherEntity(SimulatedEntity, WeatherEntity):
    """Simulated weather derived from the weather station's readings."""

    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "weather", "Weather")

    @property
    def condition(self) -> str | None:
        return self.coordinator.data.get("condition", "partlycloudy")

    @property
    def native_temperature(self) -> float | None:
        return self.coordinator.data.get("temperature_c")

    @property
    def humidity(self) -> float | None:
        return self.coordinator.data.get("humidity_pct")

    @property
    def native_pressure(self) -> float | None:
        return self.coordinator.data.get("pressure_hpa")

    @property
    def native_wind_speed(self) -> float | None:
        return self.coordinator.data.get("wind_speed_kmh")

    @property
    def wind_bearing(self) -> float | None:
        return self.coordinator.data.get("wind_bearing")

    async def async_forecast_daily(self) -> list[Forecast]:
        """Five days of plausible-looking nonsense, seeded off today's temp."""
        base = self.native_temperature or 20.0
        today = dt_util.start_of_local_day()
        # ponytail: deterministic-ish walk from the current reading, no model.
        return [
            Forecast(
                datetime=(today + timedelta(days=day)).isoformat(),
                condition=random.choice(_CONDITIONS),
                native_temperature=round(base + random.uniform(-1, 5) + day * 0.3, 1),
                native_templow=round(base - random.uniform(3, 8) + day * 0.2, 1),
                native_precipitation=round(random.uniform(0, 8), 1),
                humidity=random.randint(35, 90),
            )
            for day in range(1, 6)
        ]
