"""Dashboard generation for simulated devices."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_DASHBOARD_STORE_KEY = "lovelace.simulated_devices"
_DASHBOARDS_REGISTRY_KEY = "lovelace_dashboards"
_DASHBOARD_ID = "simulated_devices"
_DASHBOARD_URL_PATH = "simulated-devices"
_NOTIFICATION_ID = "simulated_devices_dashboard"


def _tile(entity_id: str, **extra: Any) -> dict:
    return {"type": "tile", "entity": entity_id, **extra}


def _section(title: str, cards: list[dict]) -> dict:
    return {"title": title, "cards": cards}


def _card_for_entity(entity_id: str) -> dict:
    """Return the best Lovelace card for an entity based on its domain."""
    domain = entity_id.split(".")[0]
    if domain == "climate":
        return {"type": "thermostat", "entity": entity_id}
    if domain == "media_player":
        return {"type": "media-control", "entity": entity_id}
    if domain == "alarm_control_panel":
        return {"type": "alarm-panel", "entity": entity_id}
    return _tile(entity_id)


def _is_primary(entity_id: str) -> bool:
    """Return True for the main controllable entity of a device."""
    domain = entity_id.split(".")[0]
    return domain in (
        "light", "switch", "cover", "fan", "lock", "vacuum", "valve",
        "siren", "humidifier", "climate", "media_player", "alarm_control_panel",
    )


def _build_dashboard(
    coordinators: dict,
    registry: er.EntityRegistry,
) -> dict[str, Any]:
    """Build a full Lovelace dashboard config dict."""
    sections: list[dict] = []

    for entry_id, coordinator in coordinators.items():
        entries = er.async_entries_for_config_entry(registry, entry_id)
        if not entries:
            continue

        primary_cards: list[dict] = []
        secondary_cards: list[dict] = []

        for e in sorted(entries, key=lambda x: x.entity_id):
            if e.entity_id.split(".")[0] == "button":
                continue
            card = _card_for_entity(e.entity_id)
            if _is_primary(e.entity_id):
                primary_cards.append(card)
            else:
                secondary_cards.append(card)

        all_cards = primary_cards + secondary_cards
        if all_cards:
            sections.append(_section(coordinator.device_name, all_cards))

    # Management section — always first
    management_section = _section(
        "Simulated Devices",
        [
            {
                "type": "button",
                "name": "Regenerate Dashboard",
                "icon": "mdi:view-dashboard-variant",
                "tap_action": {
                    "action": "perform-action",
                    "perform_action": f"{DOMAIN}.generate_dashboard",
                },
            },
            {
                "type": "markdown",
                "content": (
                    f"**{len(coordinators)} simulated device(s) active.**\n\n"
                    "Press above to regenerate after adding new devices."
                ),
            },
        ],
    )
    sections.insert(0, management_section)

    return {
        "views": [
            {
                "title": "Simulated Devices",
                "type": "sections",
                "sections": sections,
            }
        ]
    }


async def _save_via_lovelace_api(hass: HomeAssistant, config: dict) -> tuple[bool, bool]:
    """Update dashboard via HA's in-memory lovelace API.

    Returns (saved_live, was_new):
      saved_live — config written to in-memory API
      was_new    — dashboard entry did not exist before this call
    """
    try:
        from homeassistant.components.lovelace.const import LOVELACE_DATA  # noqa: PLC0415
        from homeassistant.components.lovelace.dashboard import LovelaceStorage  # noqa: PLC0415
    except ImportError as exc:
        _LOGGER.warning("Cannot import lovelace internals: %s", exc)
        return False, False

    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None:
        _LOGGER.warning("Lovelace component not loaded in hass.data — cannot update in-memory")
        return False, False

    dash = lovelace.dashboards.get(_DASHBOARD_URL_PATH)
    was_new = dash is None

    if was_new:
        _LOGGER.info("Dashboard '%s' not in lovelace yet — creating in-memory entry.", _DASHBOARD_URL_PATH)
        dash = LovelaceStorage(
            hass,
            {
                "id": _DASHBOARD_ID,
                "url_path": _DASHBOARD_URL_PATH,
                "title": "Simulated Devices",
                "icon": "mdi:robot-outline",
                "require_admin": False,
                "show_in_sidebar": True,
                "mode": "storage",
            },
        )
        lovelace.dashboards[_DASHBOARD_URL_PATH] = dash
        # Register the panel so it appears in the sidebar immediately.
        # This replicates what HA does at startup for each stored dashboard.
        try:
            import inspect  # noqa: PLC0415
            from homeassistant.components.frontend import async_register_built_in_panel  # noqa: PLC0415
            kwargs = dict(
                sidebar_title="Simulated Devices",
                sidebar_icon="mdi:robot-outline",
                frontend_url_path=_DASHBOARD_URL_PATH,
                require_admin=False,
                config={"mode": "storage"},
                update=False,
                show_in_sidebar=True,
            )
            if inspect.iscoroutinefunction(async_register_built_in_panel):
                await async_register_built_in_panel(hass, "lovelace", **kwargs)
            else:
                async_register_built_in_panel(hass, "lovelace", **kwargs)
            _LOGGER.info("Registered Simulated Devices panel in sidebar")
        except Exception as exc:  # noqa: BLE001
            _LOGGER.warning("Could not register frontend panel: %s", exc)

    try:
        await dash.async_save(config)
        _LOGGER.info("Simulated Devices dashboard saved successfully")
        return True, was_new
    except Exception as exc:  # noqa: BLE001
        _LOGGER.warning("Dashboard async_save failed: %s", exc, exc_info=True)
        return False, was_new


async def _ensure_dashboard_registered(hass: HomeAssistant) -> None:
    """Add dashboard entry to lovelace_dashboards storage if missing."""
    store = Store(hass, 1, _DASHBOARDS_REGISTRY_KEY, minor_version=1)
    data = await store.async_load() or {"items": []}
    if any(item.get("id") == _DASHBOARD_ID for item in data.get("items", [])):
        return
    data.setdefault("items", []).append(
        {
            "id": _DASHBOARD_ID,
            "url_path": _DASHBOARD_URL_PATH,
            "title": "Simulated Devices",
            "require_admin": False,
            "show_in_sidebar": True,
            "icon": "mdi:robot-outline",
            "mode": "storage",
        }
    )
    await store.async_save(data)


async def async_generate_dashboard(hass: HomeAssistant) -> None:
    """Generate and persist the Simulated Devices Lovelace dashboard."""
    msg: str
    try:
        coordinators: dict = hass.data.get(DOMAIN, {})
        registry = er.async_get(hass)
        config = _build_dashboard(coordinators, registry)

        # Always register in persistent storage so the dashboard survives a restart,
        # regardless of whether the live API save succeeds.
        await _ensure_dashboard_registered(hass)

        saved_live, was_new = await _save_via_lovelace_api(hass, config)

        if not saved_live:
            store = Store(hass, 1, _DASHBOARD_STORE_KEY)
            await store.async_save({"config": config})

        device_count = len(coordinators)
        if not saved_live:
            msg = (
                f"Dashboard saved with {device_count} device(s). "
                "Restart Home Assistant to activate it, then navigate to "
                "[/simulated-devices](/simulated-devices)."
            )
        elif was_new:
            msg = (
                f"Dashboard created with {device_count} device(s). "
                "Refresh your browser or navigate to "
                "[/simulated-devices](/simulated-devices)."
            )
        else:
            msg = (
                f"Dashboard regenerated with {device_count} device(s). "
                "Your browser will refresh automatically."
            )
    except Exception as exc:  # noqa: BLE001
        _LOGGER.error("Dashboard generation failed: %s", exc, exc_info=True)
        msg = f"Dashboard generation failed: {exc}\n\nCheck Home Assistant logs for details."

    await hass.services.async_call(
        "persistent_notification",
        "create",
        {
            "title": "Simulated Devices Dashboard",
            "message": msg,
            "notification_id": _NOTIFICATION_ID,
        },
    )
