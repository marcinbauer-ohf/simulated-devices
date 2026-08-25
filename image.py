"""Image platform for simulated devices."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.image import ImageEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DEVICE_TYPE_SECURITY_CAMERA
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity
from .synthetic_image import png_frame


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated image entities."""
    async_add_entities(
        SimulatedSnapshotImageEntity(hass, c)
        for c in coordinators_for(entry, DEVICE_TYPE_SECURITY_CAMERA)
    )


class SimulatedSnapshotImageEntity(SimulatedEntity, ImageEntity):
    """Last motion snapshot from the simulated camera."""

    _attr_icon = "mdi:image"
    _attr_content_type = "image/png"

    def __init__(
        self, hass: HomeAssistant, coordinator: SimulatedDeviceCoordinator
    ) -> None:
        ImageEntity.__init__(self, hass)
        super().__init__(coordinator, "snapshot", "Snapshot")

    @property
    def image_last_updated(self) -> datetime | None:
        raw = self.coordinator.data.get("last_snapshot")
        return dt_util.parse_datetime(raw) if raw else None

    async def async_image(self) -> bytes | None:
        return png_frame(int(self.coordinator.data.get("frame", 0)))
