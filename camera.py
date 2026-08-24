"""Camera platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_SECURITY_CAMERA
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity
from .synthetic_image import png_frame


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated camera entities."""
    async_add_entities(
        SimulatedCameraEntity(c)
        for c in coordinators_for(entry, DEVICE_TYPE_SECURITY_CAMERA)
    )


class SimulatedCameraEntity(SimulatedEntity, Camera):
    """Simulated camera serving a generated still image."""

    _attr_icon = "mdi:cctv"
    _attr_supported_features = CameraEntityFeature(0)

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        # CoordinatorEntity does not chain to Camera.__init__, so call it
        # explicitly before the shared init sets names and device info.
        Camera.__init__(self)
        super().__init__(coordinator, "camera", "Camera")
        self.content_type = "image/png"

    @property
    def is_recording(self) -> bool:
        return bool(self.coordinator.data.get("recording", False))

    @property
    def motion_detection_enabled(self) -> bool:
        return True

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        return png_frame(int(self.coordinator.data.get("frame", 0)))
