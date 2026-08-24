"""Scene platform for simulated devices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DEVICE_TYPE_HOME_HUB
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity

_SCENES = [("movie", "Movie Night"), ("morning", "Good Morning")]


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated scenes."""
    async_add_entities(
        SimulatedSceneEntity(coordinator, key, name)
        for coordinator in coordinators_for(entry, DEVICE_TYPE_HOME_HUB)
        for key, name in _SCENES
    )


class SimulatedSceneEntity(SimulatedEntity, Scene):
    """Simulated scene; activating it only records that it happened."""

    _attr_icon = "mdi:palette"

    def __init__(
        self, coordinator: SimulatedDeviceCoordinator, key: str, name: str
    ) -> None:
        super().__init__(coordinator, f"scene_{key}", name)
        self._scene_key = key

    async def async_activate(self, **kwargs: Any) -> None:
        self.coordinator.set_state(
            scene_applied={
                "scene": self._scene_key,
                "at": dt_util.utcnow().isoformat(),
            }
        )
