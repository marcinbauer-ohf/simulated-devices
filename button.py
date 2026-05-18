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
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    async_add_entities([SimulatedDashboardButton(coordinator)])


class SimulatedDashboardButton(SimulatedEntity, ButtonEntity):
    """Button that regenerates the Simulated Devices dashboard."""

    _attr_icon = "mdi:view-dashboard-variant"

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "generate_dashboard", "Generate Dashboard")

    async def async_press(self) -> None:
        await async_generate_dashboard(self.hass)
