"""Notify platform for simulated devices."""

from __future__ import annotations

from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DEVICE_TYPE_HOME_HUB
from .coordinator import SimulatedDeviceCoordinator, coordinators_for
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up simulated notify entities."""
    async_add_entities(
        SimulatedNotifyEntity(c) for c in coordinators_for(entry, DEVICE_TYPE_HOME_HUB)
    )


class SimulatedNotifyEntity(SimulatedEntity, NotifyEntity):
    """Simulated notifier that records the last message it was sent."""

    _attr_icon = "mdi:message-alert-outline"
    _attr_supported_features = NotifyEntityFeature.TITLE

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "notify", "Notify")

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        """Swallow the message, but keep it visible in the entity attributes."""
        self.coordinator.set_state(
            last_notification={
                "title": title,
                "message": message,
                "sent_at": dt_util.utcnow().isoformat(),
            }
        )

    @property
    def extra_state_attributes(self) -> dict | None:
        last = self.coordinator.data.get("last_notification")
        return dict(last) if last else None
