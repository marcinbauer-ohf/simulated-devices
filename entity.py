"""Base entity class for simulated devices."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .child_devices import ChildSpec, child_device_info
from .const import DEVICE_TYPES, DOMAIN
from .coordinator import SimulatedDeviceCoordinator


class SimulatedEntity(CoordinatorEntity[SimulatedDeviceCoordinator]):
    """Base class for entities created by this integration."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SimulatedDeviceCoordinator,
        entity_key: str,
        entity_name: str,
        child: ChildSpec | None = None,
    ) -> None:
        """Initialize the entity.

        Pass ``child`` to put the entity on one of the parent's child devices
        instead of on the device the config entry owns.
        """
        super().__init__(coordinator)
        self._entity_key = entity_key
        if child is not None:
            # The child device supplies "Outlet 1", so the entity is just
            # "Switch". Its own key already carries the child, so composite
            # name prefixing below never applies.
            self._attr_name = entity_name
            self._attr_unique_id = (
                f"{coordinator.config_entry.entry_id}_{child.key}_{entity_key}"
            )
            self._attr_device_info = child_device_info(
                coordinator.parent_device_id,
                coordinator.config_entry.entry_id,
                child,
            )
            return
        # On the composite device every sub-type contributes entities to the
        # same device, so keys and names must carry the sub-type to stay unique.
        if coordinator.is_composite:
            self._attr_name = f"{DEVICE_TYPES[coordinator.device_type]} {entity_name}"
            unique_key = f"{coordinator.device_type}_{entity_key}"
        else:
            self._attr_name = entity_name
            unique_key = entity_key
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{unique_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=coordinator.device_name,
            manufacturer="Simulated",
            model=DEVICE_TYPES[coordinator.entry_device_type],
            sw_version=str(coordinator.data.get("firmware_version", "1.0"))
            if coordinator.data
            else "1.0",
        )

    @property
    def available(self) -> bool:
        """Entity availability."""
        return bool(self.coordinator.data.get("connected", True))
