"""The Simulated Devices integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_DEVICE_TYPE,
    DEVICE_TYPE_EVERYTHING,
    DOMAIN,
    EVERYTHING_SUB_TYPES,
    PLATFORMS,
)
from .coordinator import SimulatedDeviceCoordinator
from .services import async_remove_services, async_setup_services

# One entry owns a list of coordinators: exactly one for a normal device, and
# one per sub-type for the composite "Everything" device.
SimulatedDevicesConfigEntry = ConfigEntry[list[SimulatedDeviceCoordinator]]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the simulated_devices integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


def _remove_dashboard_button_entities(
    hass: HomeAssistant, entry: SimulatedDevicesConfigEntry
) -> None:
    """Clean up the per-device Generate Dashboard button that 2.1.0 added.

    The dashboard is still reachable from the integration menu and from the
    simulated_devices.generate_dashboard service, so the button was redundant
    noise on every device. Without this, dropping the platform would leave its
    registry entries behind as unavailable entities.

    ponytail: delete this once nobody is upgrading from 2.1.0 any more.
    """
    registry = er.async_get(hass)
    for stale in er.async_entries_for_config_entry(registry, entry.entry_id):
        if stale.domain == "button":
            registry.async_remove(stale.entity_id)


async def async_setup_entry(
    hass: HomeAssistant, entry: SimulatedDevicesConfigEntry
) -> bool:
    """Set up simulated devices from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    _remove_dashboard_button_entities(hass, entry)

    device_type = entry.data[CONF_DEVICE_TYPE]
    sub_types = (
        EVERYTHING_SUB_TYPES
        if device_type == DEVICE_TYPE_EVERYTHING
        else (device_type,)
    )
    coordinators = [
        SimulatedDeviceCoordinator(hass, entry, sub_type) for sub_type in sub_types
    ]
    for coordinator in coordinators:
        await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinators
    entry.runtime_data = coordinators
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
