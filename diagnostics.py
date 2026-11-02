"""Diagnostics support for simulated_devices."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import SimulatedDevicesConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: SimulatedDevicesConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinators = entry.runtime_data
    first = coordinators[0]
    return {
        "device_type": first.entry_device_type,
        "device_name": first.device_name,
        "simulation_profile": first.simulation_profile,
        "sub_devices": {
            c.device_type: dict(c.data) if c.data else {} for c in coordinators
        },
    }
