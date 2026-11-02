"""Update platform for simulated devices."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add a firmware update entity to every simulated device."""
    # Device-level, like the dashboard button: one per entry, not per sub-type.
    # ponytail: availability follows sub-device 0 on the composite device;
    # only visible with random_availability on. Track all coordinators if it bites.
    async_add_entities([SimulatedUpdateEntity(entry.runtime_data[0])])


class SimulatedUpdateEntity(SimulatedEntity, UpdateEntity):
    """Simulated firmware update."""

    _attr_supported_features = (
        UpdateEntityFeature.INSTALL
        | UpdateEntityFeature.PROGRESS
        | UpdateEntityFeature.RELEASE_NOTES
    )

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "firmware", "Firmware")
        self._attr_name = "Firmware"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_firmware"

    @property
    def installed_version(self) -> str | None:
        return self.coordinator.data.get("firmware_version")

    @property
    def latest_version(self) -> str | None:
        return self.coordinator.data.get("latest_version")

    @property
    def in_progress(self) -> bool:
        return self.coordinator.data.get("update_progress") is not None

    @property
    def update_percentage(self) -> int | None:
        return self.coordinator.data.get("update_progress")

    def release_notes(self) -> str | None:
        return (
            f"Simulated firmware {self.latest_version}\n\n"
            "- Nothing actually changes, this device is not real.\n"
            "- Useful for exercising update cards and automations."
        )

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Walk the progress bar, then land on the new version."""
        target = version or self.latest_version
        for pct in (0, 25, 50, 75):
            self.coordinator.set_state(update_progress=pct)
            await asyncio.sleep(1)
        self.coordinator.set_state(
            update_progress=None,
            firmware_version=target,
            latest_version=target,
        )
