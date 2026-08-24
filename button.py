"""Button platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import SimulatedDeviceCoordinator
from .dashboard import async_generate_dashboard
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add a Generate Dashboard button to every simulated device."""
    # One button per device, not per simulated sub-type.
    # ponytail: availability follows sub-device 0 on the composite device;
    # only visible with random_availability on. Track all coordinators if it bites.
    async_add_entities([SimulatedDashboardButton(entry.runtime_data[0])])


class SimulatedDashboardButton(SimulatedEntity, ButtonEntity):
    """Button that regenerates the Simulated Devices dashboard."""

    _attr_icon = "mdi:view-dashboard-variant"

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "generate_dashboard", "Generate Dashboard")
        # Device-level button: it belongs to the entry, not to a sub-type, so
        # it keeps the plain name even on the composite device.
        self._attr_name = "Generate Dashboard"
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_generate_dashboard"
        )

    async def async_press(self) -> None:
        await async_generate_dashboard(self.hass)
