"""Remote platform for simulated devices."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.components.remote import RemoteEntity, RemoteEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DEVICE_TYPE_HOME_HUB
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity

_ACTIVITIES = ["Watch TV", "Listen to Music", "Play Game", "Movie Night"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated remote entities."""
    async_add_entities(
        SimulatedRemoteEntity(c) for c in coordinators_for(entry, DEVICE_TYPE_HOME_HUB)
    )


class SimulatedRemoteEntity(SimulatedEntity, RemoteEntity):
    """Simulated universal remote."""

    _attr_icon = "mdi:remote-tv"
    _attr_supported_features = RemoteEntityFeature.ACTIVITY
    _attr_activity_list = _ACTIVITIES

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "remote", "Remote")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("remote_on", False))

    @property
    def current_activity(self) -> str | None:
        return self.coordinator.data.get("remote_activity") if self.is_on else None

    async def async_turn_on(self, activity: str | None = None, **kwargs: Any) -> None:
        updates: dict[str, Any] = {"remote_on": True}
        if activity:
            updates["remote_activity"] = activity
        self.coordinator.set_state(**updates)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.set_state(remote_on=False)

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Commands go nowhere, but the last one stays visible for testing."""
        self.coordinator.set_state(
            last_command={
                "command": list(command),
                "sent_at": dt_util.utcnow().isoformat(),
            }
        )
