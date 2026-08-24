"""Calendar platform for simulated devices."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DEVICE_TYPE_HOME_HUB
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity

# (hour, duration_hours, summary) repeated every day
_DAILY_EVENTS = [
    (7, 1, "Morning routine"),
    (12, 1, "Lunch"),
    (18, 2, "Evening scene"),
]


def _events_between(start: datetime, end: datetime) -> list[CalendarEvent]:
    """Expand the fixed daily schedule across the requested window."""
    events: list[CalendarEvent] = []
    day = dt_util.as_local(start).replace(hour=0, minute=0, second=0, microsecond=0)
    last = dt_util.as_local(end)
    while day <= last:
        for hour, length, summary in _DAILY_EVENTS:
            event_start = day.replace(hour=hour)
            event_end = event_start + timedelta(hours=length)
            if event_end > start and event_start < end:
                events.append(
                    CalendarEvent(
                        start=event_start,
                        end=event_end,
                        summary=summary,
                        description="Simulated calendar event",
                    )
                )
        day += timedelta(days=1)
    return sorted(events, key=lambda e: e.start)


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated calendars."""
    async_add_entities(
        SimulatedCalendarEntity(c)
        for c in coordinators_for(entry, DEVICE_TYPE_HOME_HUB)
    )


class SimulatedCalendarEntity(SimulatedEntity, CalendarEntity):
    """Simulated calendar with a fixed daily schedule."""

    _attr_icon = "mdi:calendar-month"

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "calendar", "Schedule")

    @property
    def event(self) -> CalendarEvent | None:
        """The event happening now, else the next one within a week."""
        now = dt_util.now()
        upcoming = _events_between(now, now + timedelta(days=7))
        return upcoming[0] if upcoming else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return _events_between(start_date, end_date)
