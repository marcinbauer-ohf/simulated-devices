"""Cover platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_GARAGE_DOOR, DEVICE_TYPE_SMART_BLIND
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated cover entities."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    if coordinator.device_type == DEVICE_TYPE_GARAGE_DOOR:
        async_add_entities([SimulatedGarageDoorEntity(coordinator)])
    elif coordinator.device_type == DEVICE_TYPE_SMART_BLIND:
        async_add_entities([SimulatedBlindEntity(coordinator)])


class SimulatedGarageDoorEntity(SimulatedEntity, CoverEntity):
    """Simulated garage door."""

    _attr_icon = "mdi:garage"
    _attr_device_class = CoverDeviceClass.GARAGE
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "cover", "Door")

    @property
    def is_closed(self) -> bool | None:
        return not bool(self.coordinator.data["is_open"])

    @property
    def current_cover_position(self) -> int | None:
        return int(self.coordinator.data["position"])

    async def async_open_cover(self, **kwargs) -> None:
        self.coordinator.set_state(is_open=True, position=100)

    async def async_close_cover(self, **kwargs) -> None:
        self.coordinator.set_state(is_open=False, position=0)

    async def async_set_cover_position(self, **kwargs) -> None:
        pos = int(kwargs[ATTR_POSITION])
        self.coordinator.set_state(position=pos, is_open=(pos > 0))

    async def async_stop_cover(self, **kwargs) -> None:
        pass


class SimulatedBlindEntity(SimulatedEntity, CoverEntity):
    """Simulated smart blind with tilt support."""

    _attr_icon = "mdi:blinds"
    _attr_device_class = CoverDeviceClass.BLIND
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.SET_POSITION
        | CoverEntityFeature.STOP
        | CoverEntityFeature.OPEN_TILT
        | CoverEntityFeature.CLOSE_TILT
        | CoverEntityFeature.SET_TILT_POSITION
        | CoverEntityFeature.STOP_TILT
    )

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "cover", "Blind")

    @property
    def is_closed(self) -> bool | None:
        return self.coordinator.data["position"] == 0

    @property
    def current_cover_position(self) -> int | None:
        return int(self.coordinator.data["position"])

    @property
    def current_cover_tilt_position(self) -> int | None:
        return int(self.coordinator.data["tilt_position"])

    async def async_open_cover(self, **kwargs) -> None:
        self.coordinator.set_state(position=100, is_closed=False)

    async def async_close_cover(self, **kwargs) -> None:
        self.coordinator.set_state(position=0, is_closed=True)

    async def async_set_cover_position(self, **kwargs) -> None:
        pos = int(kwargs[ATTR_POSITION])
        self.coordinator.set_state(position=pos, is_closed=(pos == 0))

    async def async_open_cover_tilt(self, **kwargs) -> None:
        self.coordinator.set_state(tilt_position=100)

    async def async_close_cover_tilt(self, **kwargs) -> None:
        self.coordinator.set_state(tilt_position=0)

    async def async_set_cover_tilt_position(self, **kwargs) -> None:
        self.coordinator.set_state(tilt_position=int(kwargs[ATTR_TILT_POSITION]))

    async def async_stop_cover(self, **kwargs) -> None:
        pass

    async def async_stop_cover_tilt(self, **kwargs) -> None:
        pass
