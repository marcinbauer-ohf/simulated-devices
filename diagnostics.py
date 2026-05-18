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
    coordinator = entry.runtime_data
    return {
        "device_type": coordinator.device_type,
        "device_name": coordinator.device_name,
        "simulation_profile": coordinator.simulation_profile,
        "state": dict(coordinator.data) if coordinator.data else {},
    }
