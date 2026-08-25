"""Service registration for the simulated_devices integration."""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    FAULT_TYPES,
    SERVICE_FORCE_STATE,
    SERVICE_GENERATE_DASHBOARD,
    SERVICE_INJECT_FAULT,
    SERVICE_RESET_BATTERY,
    SERVICE_SET_PROFILE,
    SERVICE_TRIGGER_EVENT,
    SIMULATION_PROFILES,
)
from .coordinator import SimulatedDeviceCoordinator
from .dashboard import async_generate_dashboard

_SCHEMA_ENTRY_ID = vol.Schema({vol.Required("entry_id"): cv.string})

_SCHEMA_FORCE_STATE = vol.Schema(
    {
        vol.Required("entry_id"): cv.string,
        vol.Required("state_updates"): dict,
    }
)

_SCHEMA_TRIGGER_EVENT = vol.Schema(
    {
        vol.Required("entry_id"): cv.string,
        vol.Required("event_type"): cv.string,
    }
)

_SCHEMA_SET_PROFILE = vol.Schema(
    {
        vol.Required("entry_id"): cv.string,
        vol.Required("profile"): vol.In(SIMULATION_PROFILES),
    }
)

_SCHEMA_INJECT_FAULT = vol.Schema(
    {
        vol.Required("entry_id"): cv.string,
        vol.Required("fault_type"): vol.In(FAULT_TYPES),
        vol.Optional("duration_seconds", default=30): vol.All(int, vol.Range(min=1, max=3600)),
    }
)


def _get_coordinators(
    hass: HomeAssistant, call: ServiceCall
) -> list[SimulatedDeviceCoordinator]:
    """Return every coordinator behind a config entry.

    A normal device has one. The composite "Everything" device has one per
    sub-type, and a service call targets all of them.
    """
    entry_id: str = call.data["entry_id"]
    coordinators: list[SimulatedDeviceCoordinator] | None = hass.data.get(
        DOMAIN, {}
    ).get(entry_id)
    if not coordinators:
        raise ValueError(f"No simulated device with entry_id={entry_id!r}")
    return coordinators


def _applicable(
    coordinator: SimulatedDeviceCoordinator, updates: dict[str, Any]
) -> dict[str, Any]:
    """Narrow an update to keys a sub-device simulates.

    Only the composite device needs this: its sub-coordinators each hold a
    different slice of state, so an unfiltered push would scatter foreign keys
    across all of them. A single device keeps the old behaviour of accepting
    whatever it is given.
    """
    if not coordinator.is_composite:
        return updates
    return {k: v for k, v in updates.items() if k in coordinator.data}


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register all simulated_devices services."""

    async def handle_reset_battery(call: ServiceCall) -> None:
        for coordinator in _get_coordinators(hass, call):
            if "battery" in coordinator.data:
                coordinator.set_state(battery=100.0)

    async def handle_force_state(call: ServiceCall) -> None:
        updates = call.data["state_updates"]
        for coordinator in _get_coordinators(hass, call):
            if applicable := _applicable(coordinator, updates):
                coordinator.set_state(**applicable)

    async def handle_trigger_event(call: ServiceCall) -> None:
        event_type = call.data["event_type"]
        now = dt_util.utcnow().isoformat()
        for coordinator in _get_coordinators(hass, call):
            coordinator.set_state(
                last_event=event_type,
                last_event_time=now,
                last_press_time=now,
            )

    async def handle_set_profile(call: ServiceCall) -> None:
        for coordinator in _get_coordinators(hass, call):
            coordinator.simulation_profile = call.data["profile"]

    async def handle_inject_fault(call: ServiceCall) -> None:
        fault_type = call.data["fault_type"]
        duration = call.data["duration_seconds"]
        fault_state = FAULT_TYPES.get(fault_type, {})
        coordinators = _get_coordinators(hass, call)
        for coordinator in coordinators:
            if applicable := _applicable(coordinator, fault_state):
                coordinator.set_state(**applicable)

        async def _auto_clear() -> None:
            await asyncio.sleep(duration)
            for coordinator in coordinators:
                clear_state = {
                    k: (False if isinstance(v, bool) else v)
                    for k, v in _applicable(coordinator, fault_state).items()
                }
                if not clear_state:
                    continue
                # Restore connected=True and battery to a reasonable value
                if "connected" in clear_state:
                    clear_state["connected"] = True
                if "battery" in clear_state:
                    clear_state["battery"] = coordinator.data.get("battery", 5.0)
                coordinator.set_state(**clear_state)

        hass.async_create_task(_auto_clear())

    async def handle_generate_dashboard(call: ServiceCall) -> None:
        await async_generate_dashboard(hass)

    hass.services.async_register(
        DOMAIN, SERVICE_GENERATE_DASHBOARD, handle_generate_dashboard, schema=vol.Schema({})
    )
    hass.services.async_register(
        DOMAIN, SERVICE_RESET_BATTERY, handle_reset_battery, schema=_SCHEMA_ENTRY_ID
    )
    hass.services.async_register(
        DOMAIN, SERVICE_FORCE_STATE, handle_force_state, schema=_SCHEMA_FORCE_STATE
    )
    hass.services.async_register(
        DOMAIN, SERVICE_TRIGGER_EVENT, handle_trigger_event, schema=_SCHEMA_TRIGGER_EVENT
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SET_PROFILE, handle_set_profile, schema=_SCHEMA_SET_PROFILE
    )
    hass.services.async_register(
        DOMAIN, SERVICE_INJECT_FAULT, handle_inject_fault, schema=_SCHEMA_INJECT_FAULT
    )


async def async_remove_services(hass: HomeAssistant) -> None:
    """Remove all simulated_devices services."""
    for service in (
        SERVICE_GENERATE_DASHBOARD,
        SERVICE_RESET_BATTERY,
        SERVICE_FORCE_STATE,
        SERVICE_TRIGGER_EVENT,
        SERVICE_SET_PROFILE,
        SERVICE_INJECT_FAULT,
    ):
        hass.services.async_remove(DOMAIN, service)
