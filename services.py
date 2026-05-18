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


def _get_coordinator(hass: HomeAssistant, call: ServiceCall) -> SimulatedDeviceCoordinator:
    entry_id: str = call.data["entry_id"]
    coordinator: SimulatedDeviceCoordinator | None = hass.data.get(DOMAIN, {}).get(entry_id)
    if coordinator is None:
        raise ValueError(f"No simulated device with entry_id={entry_id!r}")
    return coordinator


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register all simulated_devices services."""

    async def handle_reset_battery(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        coordinator.set_state(battery=100.0)

    async def handle_force_state(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        coordinator.set_state(**call.data["state_updates"])

    async def handle_trigger_event(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        event_type = call.data["event_type"]
        coordinator.set_state(
            last_event=event_type,
            last_event_time=dt_util.utcnow().isoformat(),
            last_press_time=dt_util.utcnow().isoformat(),
        )

    async def handle_set_profile(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        coordinator.simulation_profile = call.data["profile"]

    async def handle_inject_fault(call: ServiceCall) -> None:
        coordinator = _get_coordinator(hass, call)
        fault_type = call.data["fault_type"]
        duration = call.data["duration_seconds"]
        fault_state = FAULT_TYPES.get(fault_type, {})
        coordinator.set_state(**fault_state)

        async def _auto_clear() -> None:
            await asyncio.sleep(duration)
            clear_state = {k: (False if isinstance(v, bool) else v) for k, v in fault_state.items()}
            # Restore connected=True and battery to reasonable value if those were faulted
            if "connected" in clear_state:
                clear_state["connected"] = True
            if "battery" in fault_state:
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
