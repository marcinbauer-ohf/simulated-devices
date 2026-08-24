"""Datetime platform for simulated devices."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DEVICE_TYPE_HOME_HUB
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated datetime entities."""
    async_add_entities(
        SimulatedDateTimeEntity(c)
        for c in coordinators_for(entry, DEVICE_TYPE_HOME_HUB)
    )


class SimulatedDateTimeEntity(SimulatedEntity, DateTimeEntity):
    """Simulated timestamp field, e.g. the next scheduled run."""

    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "next_run", "Next Run")

    @property
    def native_value(self) -> datetime | None:
        raw = self.coordinator.data.get("datetime_value")
        if not raw:
            return None
        # HA requires an aware datetime; stored values are local wall time.
        parsed = dt_util.parse_datetime(raw)
        return dt_util.as_utc(parsed) if parsed else None

    async def async_set_value(self, value: datetime) -> None:
        self.coordinator.set_state(
            datetime_value=dt_util.as_local(value).replace(microsecond=0).isoformat()
        )
