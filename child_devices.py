"""Child (sub-)device definitions for the parent/child device types.

Core 2026.12 added child devices: one physical product split into logical
parts, e.g. the outlets of a power strip. The parent device must exist in the
registry before its children, so this module registers both up front in
async_setup_entry — entities then only reference them.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import (
    DEVICE_TYPE_CHILD_TEST_RIG,
    DEVICE_TYPE_DUAL_LENS_CAMERA,
    DEVICE_TYPE_POWER_STRIP,
    DEVICE_TYPE_WALL_SWITCH_2GANG,
    DEVICE_TYPES,
    DOMAIN,
)


@dataclass(frozen=True)
class ChildSpec:
    """One child device of a simulated parent."""

    key: str
    name: str | None = None
    disabled_by_default: bool = False

    def state_key(self, suffix: str) -> str:
        """Key this child's value lives under in the coordinator data."""
        return f"{self.key}_{suffix}"


OUTLETS: tuple[ChildSpec, ...] = tuple(
    ChildSpec(f"outlet_{n}", f"Outlet {n}") for n in (1, 2, 3, 4)
)

LENSES: tuple[ChildSpec, ...] = (
    ChildSpec("wide_lens", "Wide lens"),
    ChildSpec("telephoto_lens", "Telephoto lens"),
)

GANGS: tuple[ChildSpec, ...] = (
    ChildSpec("gang_left", "Left"),
    ChildSpec("gang_right", "Right"),
)

# Edge cases for the frontend's sub-device UI. The rig parent deliberately has
# no entities of its own.
RIG_NORMAL = ChildSpec("rig_normal", "Normal child")
RIG_DIAGNOSTIC = ChildSpec("rig_diagnostic", "Diagnostics only")
RIG_DISABLED = ChildSpec("rig_disabled", "Disabled by default", disabled_by_default=True)
# No name and no translation key: a translation key without a matching string
# renders as the raw key, which is not the empty heading we want to test.
RIG_NAMELESS = ChildSpec("rig_nameless")
RIG_CHILDREN: tuple[ChildSpec, ...] = (
    RIG_NORMAL,
    RIG_DIAGNOSTIC,
    RIG_DISABLED,
    RIG_NAMELESS,
)

CHILDREN: dict[str, tuple[ChildSpec, ...]] = {
    DEVICE_TYPE_POWER_STRIP: OUTLETS,
    DEVICE_TYPE_DUAL_LENS_CAMERA: LENSES,
    DEVICE_TYPE_WALL_SWITCH_2GANG: GANGS,
    DEVICE_TYPE_CHILD_TEST_RIG: RIG_CHILDREN,
}


def supports_child_devices() -> bool:
    """Whether the installed core knows about child devices."""
    return hasattr(dr, "ChildDeviceInfo")


def child_device_info(parent_device_id: str, entry_id: str, child: ChildSpec):
    """Device info pointing an entity at one child device."""
    return dr.ChildDeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_{child.key}")},
        name=child.name,
        parent_device_id=parent_device_id,
    )


def async_register_devices(
    hass: HomeAssistant, entry: ConfigEntry, coordinator
) -> None:
    """Register the parent device and its children.

    Platforms are set up concurrently, so a child entity can reach the registry
    before any parent entity does — and a parent with no entities of its own
    would never be created at all. Both are registered here instead.
    """
    registry = dr.async_get(hass)
    parent = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=coordinator.device_name,
        manufacturer="Simulated",
        model=DEVICE_TYPES[coordinator.entry_device_type],
        sw_version=str(coordinator.data.get("firmware_version", "1.0")),
    )
    coordinator.parent_device_id = parent.id

    for child in CHILDREN[coordinator.device_type]:
        registry.async_get_or_create_child(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, f"{entry.entry_id}_{child.key}")},
            name=child.name,
            parent_device_id=parent.id,
            # Only applied when the child device is created, so a user who
            # enables it keeps it enabled across restarts.
            disabled_by=dr.DeviceEntryDisabler.INTEGRATION
            if child.disabled_by_default
            else None,
        )
