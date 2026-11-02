"""Camera platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .child_devices import LENSES, ChildSpec
from .const import DEVICE_TYPE_DUAL_LENS_CAMERA, DEVICE_TYPE_SECURITY_CAMERA
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
        [
            SimulatedCameraEntity(c)
            for c in coordinators_for(entry, DEVICE_TYPE_SECURITY_CAMERA)
        ]
        + [
            SimulatedCameraEntity(c, lens, frame_offset=offset)
            for c in coordinators_for(entry, DEVICE_TYPE_DUAL_LENS_CAMERA)
            for offset, lens in enumerate(LENSES)
        ]
    )


class SimulatedCameraEntity(SimulatedEntity, Camera):
    """Simulated camera serving a generated still image."""

    _attr_icon = "mdi:cctv"
    _attr_supported_features = CameraEntityFeature(0)

    def __init__(
        self,
        coordinator: SimulatedDeviceCoordinator,
        child: ChildSpec | None = None,
        frame_offset: int = 0,
    ) -> None:
        # CoordinatorEntity does not chain to Camera.__init__, so call it
        # explicitly before the shared init sets names and device info.
        Camera.__init__(self)
        super().__init__(coordinator, "camera", "Camera", child=child)
        self.content_type = "image/png"
        # Offsets the sweeping bar so two lenses never show the same frame.
        self._frame_offset = frame_offset * 11

    @property
    def is_recording(self) -> bool:
        return bool(self.coordinator.data.get("recording", False))

    @property
    def motion_detection_enabled(self) -> bool:
        return True

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        if self.coordinator.data.get("privacy_mode"):
            return None
        return png_frame(
            int(self.coordinator.data.get("frame", 0)) + self._frame_offset
        )
