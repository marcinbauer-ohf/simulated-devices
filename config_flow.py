"""Config flow for simulated_devices integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import zeroconf
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.util import slugify

from .const import (
    CONF_DEVICE_TYPE,
    CONF_RANDOM_AVAILABILITY,
    CONF_RANDOM_UPDATES,
    CONF_SIMULATION_PROFILE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_DEVICE_NAME,
    DEFAULT_RANDOM_AVAILABILITY,
    DEFAULT_RANDOM_UPDATES,
    DEFAULT_SIMULATION_PROFILE,
    DEFAULT_UPDATE_INTERVAL,
    DEVICE_TYPES,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    SIMULATION_PROFILES,
    ZEROCONF_PROP_DEVICE_TYPE,
    ZEROCONF_PROP_NAME,
    ZEROCONF_PROP_UNIQUE_ID,
    ZEROCONF_SERVICE_TYPE,
)


def _device_type_selector(default: str) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=k, label=v)
                for k, v in DEVICE_TYPES.items()
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _simulation_profile_selector(default: str) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=k, label=v)
                for k, v in SIMULATION_PROFILES.items()
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _build_data_schema(
    *,
    name: str = DEFAULT_DEVICE_NAME,
    device_type: str,
    update_interval: int = DEFAULT_UPDATE_INTERVAL,
    random_updates: bool = DEFAULT_RANDOM_UPDATES,
    random_availability: bool = DEFAULT_RANDOM_AVAILABILITY,
) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=name): str,
            vol.Required(CONF_DEVICE_TYPE, default=device_type): _device_type_selector(device_type),
            vol.Required(CONF_UPDATE_INTERVAL, default=update_interval): vol.All(
                vol.Coerce(int),
                vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
            ),
            vol.Required(CONF_RANDOM_UPDATES, default=random_updates): bool,
            vol.Required(CONF_RANDOM_AVAILABILITY, default=random_availability): bool,
        }
    )


def _get_zeroconf_property(
    discovery_info: zeroconf.ZeroconfServiceInfo, key: str
) -> str | None:
    properties = discovery_info.properties
    if not properties:
        return None
    value = properties.get(key)
    if value is None:
        value = properties.get(key.encode())
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode(errors="ignore")
    return str(value)


def _get_discovered_name(discovery_info: zeroconf.ZeroconfServiceInfo) -> str:
    name_from_properties = _get_zeroconf_property(discovery_info, ZEROCONF_PROP_NAME)
    if name_from_properties:
        return name_from_properties
    return (
        discovery_info.name.removesuffix(ZEROCONF_SERVICE_TYPE).rstrip(".")
        or DEFAULT_DEVICE_NAME
    )


def _get_discovered_device_type(discovery_info: zeroconf.ZeroconfServiceInfo) -> str:
    raw = _get_zeroconf_property(discovery_info, ZEROCONF_PROP_DEVICE_TYPE)
    if raw in DEVICE_TYPES:
        return raw
    return next(iter(DEVICE_TYPES))


class SimulatedDevicesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Simulated Devices."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_defaults: dict[str, Any] | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return self.async_show_menu(
            step_id="user",
            menu_options=["single", "batch", "generate_dashboard", "remove_all"],
        )

    async def async_step_remove_all(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        existing = self.hass.config_entries.async_entries(DOMAIN)
        if user_input is not None:
            for entry in existing:
                await self.hass.config_entries.async_remove(entry.entry_id)
            return self.async_abort(reason="all_devices_removed")

        return self.async_show_form(
            step_id="remove_all",
            data_schema=vol.Schema({}),
            description_placeholders={"count": str(len(existing))},
        )

    async def async_step_generate_dashboard(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        import logging  # noqa: PLC0415
        _log = logging.getLogger(__name__)
        try:
            from .dashboard import async_generate_dashboard  # noqa: PLC0415
            await async_generate_dashboard(self.hass)
        except Exception as exc:  # noqa: BLE001
            _log.error("Dashboard generation failed: %s", exc, exc_info=True)
        return self.async_abort(reason="dashboard_generated")

    async def async_step_single(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            unique_id = f"{user_input[CONF_DEVICE_TYPE]}_{slugify(user_input[CONF_NAME])}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="single",
            data_schema=_build_data_schema(device_type=next(iter(DEVICE_TYPES))),
        )

    async def async_step_batch(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            prefix = user_input.get("name_prefix", "").strip()
            interval = user_input[CONF_UPDATE_INTERVAL]
            for device_type, display_name in DEVICE_TYPES.items():
                name = f"{prefix} {display_name}".strip() if prefix else display_name
                self.hass.async_create_task(
                    self.hass.config_entries.flow.async_init(
                        DOMAIN,
                        context={"source": "import"},
                        data={
                            CONF_NAME: name,
                            CONF_DEVICE_TYPE: device_type,
                            CONF_UPDATE_INTERVAL: interval,
                            CONF_RANDOM_UPDATES: DEFAULT_RANDOM_UPDATES,
                            CONF_RANDOM_AVAILABILITY: DEFAULT_RANDOM_AVAILABILITY,
                        },
                    )
                )
            return self.async_abort(reason="batch_initiated")

        return self.async_show_form(
            step_id="batch",
            data_schema=vol.Schema(
                {
                    vol.Optional("name_prefix", default="Sim"): str,
                    vol.Required(
                        CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                }
            ),
        )

    async def async_step_import(
        self, user_input: dict[str, Any]
    ) -> FlowResult:
        unique_id = f"{user_input[CONF_DEVICE_TYPE]}_{slugify(user_input[CONF_NAME])}"
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        discovered_name = _get_discovered_name(discovery_info)
        discovered_device_type = _get_discovered_device_type(discovery_info)
        discovered_unique = (
            _get_zeroconf_property(discovery_info, ZEROCONF_PROP_UNIQUE_ID)
            or discovery_info.hostname
            or discovery_info.name
        )

        await self.async_set_unique_id(f"zeroconf_{slugify(discovered_unique)}")
        self._abort_if_unique_id_configured()

        self._discovered_defaults = {
            CONF_NAME: discovered_name,
            CONF_DEVICE_TYPE: discovered_device_type,
            CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL,
            CONF_RANDOM_UPDATES: DEFAULT_RANDOM_UPDATES,
            CONF_RANDOM_AVAILABILITY: DEFAULT_RANDOM_AVAILABILITY,
        }
        self.context["title_placeholders"] = {CONF_NAME: discovered_name}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if self._discovered_defaults is None:
            return self.async_abort(reason="no_discovery_data")

        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={CONF_NAME: self._discovered_defaults[CONF_NAME]},
            data_schema=_build_data_schema(
                name=self._discovered_defaults[CONF_NAME],
                device_type=self._discovered_defaults[CONF_DEVICE_TYPE],
                update_interval=self._discovered_defaults[CONF_UPDATE_INTERVAL],
                random_updates=self._discovered_defaults[CONF_RANDOM_UPDATES],
                random_availability=self._discovered_defaults[CONF_RANDOM_AVAILABILITY],
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> SimulatedDevicesOptionsFlow:
        return SimulatedDevicesOptionsFlow(config_entry)


class SimulatedDevicesOptionsFlow(OptionsFlow):
    """Handle an options flow for Simulated Devices."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self.config_entry.options
        data = self.config_entry.data

        def _get(key: str, default: Any) -> Any:
            return opts.get(key, data.get(key, default))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=_get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                    vol.Required(
                        CONF_RANDOM_UPDATES,
                        default=_get(CONF_RANDOM_UPDATES, DEFAULT_RANDOM_UPDATES),
                    ): bool,
                    vol.Required(
                        CONF_RANDOM_AVAILABILITY,
                        default=_get(CONF_RANDOM_AVAILABILITY, DEFAULT_RANDOM_AVAILABILITY),
                    ): bool,
                    vol.Required(
                        CONF_SIMULATION_PROFILE,
                        default=_get(CONF_SIMULATION_PROFILE, DEFAULT_SIMULATION_PROFILE),
                    ): _simulation_profile_selector(
                        _get(CONF_SIMULATION_PROFILE, DEFAULT_SIMULATION_PROFILE)
                    ),
                }
            ),
        )
