"""The Simulated Devices integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import SimulatedDeviceCoordinator
from .services import async_remove_services, async_setup_services

SimulatedDevicesConfigEntry = ConfigEntry[SimulatedDeviceCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the simulated_devices integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: SimulatedDevicesConfigEntry
) -> bool:
    """Set up simulated devices from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = SimulatedDeviceCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services once (idempotent — HA ignores duplicate registrations)
    await async_setup_services(hass)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: SimulatedDevicesConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        # Remove services when last entry is unloaded
        if not hass.data[DOMAIN]:
            await async_remove_services(hass)
    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant, entry: SimulatedDevicesConfigEntry
) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
