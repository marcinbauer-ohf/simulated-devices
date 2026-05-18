"""Light platform for simulated devices."""

from __future__ import annotations

import colorsys
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_TYPE_SMART_LIGHT
from .coordinator import SimulatedDeviceCoordinator
from .entity import SimulatedEntity

_EFFECTS = ["none", "colorloop", "flash", "random", "strobe"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the simulated light for a config entry."""
    coordinator: SimulatedDeviceCoordinator = entry.runtime_data
    if coordinator.device_type != DEVICE_TYPE_SMART_LIGHT:
        return
    async_add_entities([SimulatedLightEntity(coordinator)])


class SimulatedLightEntity(SimulatedEntity, LightEntity):
    """Simulated light with full color support."""

    _attr_icon = "mdi:lightbulb"
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.HS}
    _attr_min_color_temp_kelvin = 2000   # 500 mireds = warm
    _attr_max_color_temp_kelvin = 6500   # 153 mireds = cool
    _attr_effect_list = _EFFECTS
    _attr_supported_features = LightEntityFeature.EFFECT | LightEntityFeature.TRANSITION

    def __init__(self, coordinator: SimulatedDeviceCoordinator) -> None:
        super().__init__(coordinator, "light", "Light")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get("is_on", False))

    @property
    def color_mode(self) -> ColorMode:
        return ColorMode.HS

    @property
    def brightness(self) -> int | None:
        if not self.is_on:
            return None
        return int(self.coordinator.data.get("brightness", 200))

    @property
    def color_temp_kelvin(self) -> int | None:
        return int(self.coordinator.data.get("color_temp_kelvin", 4000))

    @property
    def hs_color(self) -> tuple[float, float] | None:
        hs = self.coordinator.data.get("hs_color", [30.0, 70.0])
        return (float(hs[0]), float(hs[1]))

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        hs = self.hs_color
        if hs is None:
            return None
        r, g, b = colorsys.hsv_to_rgb(hs[0] / 360, hs[1] / 100, 1.0)
        return (int(r * 255), int(g * 255), int(b * 255))

    @property
    def effect(self) -> str | None:
        return self.coordinator.data.get("effect", "none")

    async def async_turn_on(self, **kwargs: Any) -> None:
        updates: dict = {"is_on": True}
        if ATTR_BRIGHTNESS in kwargs:
            updates["brightness"] = max(1, min(255, int(kwargs[ATTR_BRIGHTNESS])))
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            updates["color_temp_kelvin"] = max(2000, min(6500, int(kwargs[ATTR_COLOR_TEMP_KELVIN])))
        if ATTR_HS_COLOR in kwargs:
            h, s = kwargs[ATTR_HS_COLOR]
            updates["hs_color"] = [round(float(h) % 360, 1), round(max(0.0, min(100.0, float(s))), 1)]
        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
            h, s, _ = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            updates["hs_color"] = [round(h * 360, 1), round(s * 100, 1)]
        if ATTR_EFFECT in kwargs:
            updates["effect"] = kwargs[ATTR_EFFECT]
        self.coordinator.set_state(**updates)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.coordinator.set_state(is_on=False)
