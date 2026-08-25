"""Device tracker platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_PHONE_TRACKER
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated device tracker entities."""
    async_add_entities(
        SimulatedDeviceTrackerEntity(c)
        for c in coordinators_for(entry, DEVICE_TYPE_PHONE_TRACKER)
    )


class SimulatedDeviceTrackerEntity(SimulatedEntity, TrackerEntity):
    """Simulated GPS tracker that wanders around the configured home."""

    _attr_icon = "mdi:cellphone"
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "tracker", "Tracker")

    @property
    def latitude(self) -> float | None:
        return self.coordinator.data.get("latitude")

    @property
    def longitude(self) -> float | None:
        return self.coordinator.data.get("longitude")

    @property
    def location_accuracy(self) -> int:
        return int(self.coordinator.data.get("gps_accuracy", 20))

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        # HA resolves home/not_home from the coordinates itself; this just
        # exposes where the simulation thinks the device is headed.
        return {"simulated_location": self.coordinator.data.get("location_name", "")}
