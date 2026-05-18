"""Base entity class for simulated devices."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEVICE_TYPES, DOMAIN
from .coordinator import SimulatedDeviceCoordinator


class SimulatedEntity(CoordinatorEntity[SimulatedDeviceCoordinator]):
    """Base class for entities created by this integration."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: SimulatedDeviceCoordinator, entity_key: str, entity_name: str
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entity_key = entity_key
        self._attr_name = entity_name
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=coordinator.device_name,
            manufacturer="Simulated",
            model=DEVICE_TYPES[coordinator.device_type],
            sw_version="1.0",
        )

    @property
    def available(self) -> bool:
        """Entity availability."""
        return bool(self.coordinator.data.get("connected", True))
