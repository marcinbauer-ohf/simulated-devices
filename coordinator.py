"""Data coordinator for simulated devices."""

from __future__ import annotations

import math
import random
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    BATTERY_DRAIN_RATES,
    CONF_DEVICE_TYPE,
    CONF_RANDOM_AVAILABILITY,
    CONF_RANDOM_UPDATES,
    CONF_SIMULATION_PROFILE,
    CONF_UPDATE_INTERVAL,
    DEFAULT_RANDOM_AVAILABILITY,
    DEFAULT_RANDOM_UPDATES,
    DEFAULT_SIMULATION_PROFILE,
    DEFAULT_UPDATE_INTERVAL,
    DEVICE_TYPE_AIR_QUALITY,
    DEVICE_TYPE_ALARM_PANEL,
    DEVICE_TYPE_BUTTON_DEVICE,
    DEVICE_TYPE_DOOR_WINDOW_SENSOR,
    DEVICE_TYPE_DOORBELL,
    DEVICE_TYPE_ENERGY_METER,
    DEVICE_TYPE_EV_CHARGER,
    DEVICE_TYPE_GARAGE_DOOR,
    DEVICE_TYPE_HUMIDIFIER,
    DEVICE_TYPE_MEDIA_PLAYER,
    DEVICE_TYPE_MOTION_SENSOR,
    DEVICE_TYPE_ROBOT_VACUUM,
    DEVICE_TYPE_SIREN,
    DEVICE_TYPE_SMART_BLIND,
    DEVICE_TYPE_SMART_FAN,
    DEVICE_TYPE_SMART_LIGHT,
    DEVICE_TYPE_SMART_LOCK,
    DEVICE_TYPE_SMART_PLUG,
    DEVICE_TYPE_SMART_VALVE,
    DEVICE_TYPE_SMOKE_CO_DETECTOR,
    DEVICE_TYPE_SOLAR_PANEL,
    DEVICE_TYPE_THERMOSTAT,
    DEVICE_TYPE_WATER_LEAK,
    DEVICE_TYPE_WEATHER_STATION,
    DOMAIN,
    SIM_PROFILE_AWAY,
    SIM_PROFILE_HOME,
    SIM_PROFILE_NIGHT,
    SIM_PROFILE_RANDOM,
)

import logging

_LOGGER = logging.getLogger(__name__)

# (artist, album, title) tuples
_MEDIA_TRACKS = [
    ("Queen", "A Night at the Opera", "Bohemian Rhapsody"),
    ("Eagles", "Hotel California", "Hotel California"),
    ("Led Zeppelin", "Led Zeppelin IV", "Stairway to Heaven"),
    ("John Lennon", "Imagine", "Imagine"),
    ("Nirvana", "Nevermind", "Smells Like Teen Spirit"),
    ("Bob Dylan", "Highway 61 Revisited", "Like a Rolling Stone"),
    ("Prince", "Purple Rain", "Purple Rain"),
    ("Marvin Gaye", "What's Going On", "What's Going On"),
    ("David Bowie", "Ziggy Stardust", "Starman"),
    ("Pink Floyd", "The Dark Side of the Moon", "Money"),
    ("Fleetwood Mac", "Rumours", "Go Your Own Way"),
    ("The Beatles", "Abbey Road", "Come Together"),
]


class SimulatedDeviceCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator managing state for one simulated device."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.config_entry = entry
        self.device_type: str = entry.data[CONF_DEVICE_TYPE]
        self.device_name: str = entry.title
        self.simulation_profile: str = self._get_option_raw(
            entry, CONF_SIMULATION_PROFILE, DEFAULT_SIMULATION_PROFILE
        )
        self._alarm_trigger_count: int = 0
        self._vacuum_tick: int = 0

        update_interval = timedelta(
            seconds=self._get_option_raw(entry, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=update_interval,
        )

    @staticmethod
    def _get_option_raw(entry: ConfigEntry, key: str, default: Any) -> Any:
        return entry.options.get(key, entry.data.get(key, default))

    def _get_option(self, key: str, default: Any) -> Any:
        return self._get_option_raw(self.config_entry, key, default)

    @property
    def random_updates(self) -> bool:
        return bool(self._get_option(CONF_RANDOM_UPDATES, DEFAULT_RANDOM_UPDATES))

    @property
    def random_availability(self) -> bool:
        return bool(self._get_option(CONF_RANDOM_AVAILABILITY, DEFAULT_RANDOM_AVAILABILITY))

    # ------------------------------------------------------------------
    # Profile helpers
    # ------------------------------------------------------------------

    def _get_hour(self) -> int:
        return dt_util.now().hour

    def _motion_probability(self) -> float:
        hour = self._get_hour()
        if self.simulation_profile == SIM_PROFILE_HOME:
            return 0.12 if 7 <= hour <= 22 else 0.02
        if self.simulation_profile == SIM_PROFILE_AWAY:
            return 0.005
        if self.simulation_profile == SIM_PROFILE_NIGHT:
            return 0.01
        return 0.05

    def _light_on_probability(self) -> float:
        hour = self._get_hour()
        if self.simulation_profile == SIM_PROFILE_HOME:
            return 0.15 if 17 <= hour <= 23 else 0.03
        if self.simulation_profile == SIM_PROFILE_AWAY:
            return 0.01
        if self.simulation_profile == SIM_PROFILE_NIGHT:
            return 0.0
        return 0.05

    def _comfort_temp(self) -> float:
        if self.simulation_profile == SIM_PROFILE_AWAY:
            return 18.0
        if self.simulation_profile == SIM_PROFILE_NIGHT:
            return 19.0
        return 21.0

    # ------------------------------------------------------------------
    # Initial state builders
    # ------------------------------------------------------------------

    def _build_initial_state(self) -> dict[str, Any]:
        base: dict[str, Any] = {"connected": True}
        drain_rate = BATTERY_DRAIN_RATES.get(self.device_type)
        if drain_rate is not None:
            base["battery"] = 100.0

        builders = {
            DEVICE_TYPE_SMART_LIGHT: self._init_smart_light,
            DEVICE_TYPE_SMART_PLUG: self._init_smart_plug,
            DEVICE_TYPE_WEATHER_STATION: self._init_weather_station,
            DEVICE_TYPE_GARAGE_DOOR: self._init_garage_door,
            DEVICE_TYPE_THERMOSTAT: self._init_thermostat,
            DEVICE_TYPE_HUMIDIFIER: self._init_humidifier,
            DEVICE_TYPE_SMART_LOCK: self._init_smart_lock,
            DEVICE_TYPE_MOTION_SENSOR: self._init_motion_sensor,
            DEVICE_TYPE_DOOR_WINDOW_SENSOR: self._init_door_window,
            DEVICE_TYPE_SMOKE_CO_DETECTOR: self._init_smoke_co,
            DEVICE_TYPE_ALARM_PANEL: self._init_alarm_panel,
            DEVICE_TYPE_SIREN: self._init_siren,
            DEVICE_TYPE_WATER_LEAK: self._init_water_leak,
            DEVICE_TYPE_DOORBELL: self._init_doorbell,
            DEVICE_TYPE_MEDIA_PLAYER: self._init_media_player,
            DEVICE_TYPE_SMART_FAN: self._init_smart_fan,
            DEVICE_TYPE_AIR_QUALITY: self._init_air_quality,
            DEVICE_TYPE_ROBOT_VACUUM: self._init_robot_vacuum,
            DEVICE_TYPE_SMART_BLIND: self._init_smart_blind,
            DEVICE_TYPE_SMART_VALVE: self._init_smart_valve,
            DEVICE_TYPE_ENERGY_METER: self._init_energy_meter,
            DEVICE_TYPE_EV_CHARGER: self._init_ev_charger,
            DEVICE_TYPE_SOLAR_PANEL: self._init_solar_panel,
            DEVICE_TYPE_BUTTON_DEVICE: self._init_button_device,
        }
        builder = builders.get(self.device_type)
        if builder:
            base.update(builder())
        return base

    def _init_smart_light(self) -> dict:
        return {
            "is_on": False,
            "brightness": 200,
            "color_temp_kelvin": 4000,
            "hs_color": [30.0, 70.0],
            "effect": "none",
        }

    def _init_smart_plug(self) -> dict:
        return {"is_on": False, "power_w": 0.0, "energy_kwh": 0.0}

    def _init_weather_station(self) -> dict:
        return {"temperature_c": 21.5, "humidity_pct": 45.0}

    def _init_garage_door(self) -> dict:
        return {"is_open": False, "position": 0, "obstruction": False}

    def _init_thermostat(self) -> dict:
        return {
            "hvac_mode": "heat",
            "hvac_action": "idle",
            "target_temp": 21.0,
            "current_temp": 20.5,
            "current_humidity": 48.0,
            "preset_mode": "home",
            "fan_mode": "auto",
            "swing_mode": "off",
        }

    def _init_humidifier(self) -> dict:
        return {
            "is_on": False,
            "target_humidity": 50,
            "current_humidity": 47.0,
            "mode": "auto",
            "water_level_pct": 100.0,
        }

    def _init_smart_lock(self) -> dict:
        return {"lock_state": "locked", "door_contact": False}

    def _init_motion_sensor(self) -> dict:
        return {"motion": False, "tamper": False, "illuminance_lx": 150.0}

    def _init_door_window(self) -> dict:
        return {"contact": True, "tamper": False, "temperature_c": 20.0}

    def _init_smoke_co(self) -> dict:
        return {
            "smoke": False,
            "carbon_monoxide": False,
            "battery_low": False,
            "co_ppm": 0.0,
        }

    def _init_alarm_panel(self) -> dict:
        return {"alarm_state": "disarmed"}

    def _init_siren(self) -> dict:
        return {"is_on": False, "tone": "default", "volume_level": 1.0}

    def _init_water_leak(self) -> dict:
        return {"moisture": False, "battery_low": False, "temperature_c": 19.5}

    def _init_doorbell(self) -> dict:
        return {"motion": False, "last_press_time": None}

    def _init_media_player(self) -> dict:
        return {
            "state": "idle",
            "volume_level": 0.3,
            "is_volume_muted": False,
            "media_title": None,
            "media_artist": None,
            "media_album_name": None,
            "media_duration": None,
            "media_position": 0,
            "source": "Spotify",
            "source_list": ["Spotify", "Radio", "TV", "Bluetooth"],
            "shuffle": False,
            "repeat": "off",
            "sound_mode": "Normal",
            "sound_mode_list": ["Normal", "Movie", "Music", "Night", "Sports"],
        }

    def _init_smart_fan(self) -> dict:
        return {
            "is_on": False,
            "percentage": 50,
            "oscillating": False,
            "preset_mode": "normal",
            "direction": "forward",
        }

    def _init_air_quality(self) -> dict:
        return {
            "pm25_ugm3": 8.0,
            "pm10_ugm3": 12.0,
            "co2_ppm": 420.0,
            "voc_index": 100,
            "aqi": 35,
            "temperature_c": 22.0,
            "humidity_pct": 47.0,
        }

    def _init_robot_vacuum(self) -> dict:
        return {
            "status": "docked",
            "fan_speed": "normal",
            "battery": 100.0,
            "cleaned_area_m2": 0.0,
        }

    def _init_smart_blind(self) -> dict:
        return {"is_closed": True, "position": 0, "tilt_position": 50}

    def _init_smart_valve(self) -> dict:
        return {
            "is_open": False,
            "flow_rate_lpm": 0.0,
            "volume_l": 0.0,
            "leak_detected": False,
        }

    def _init_energy_meter(self) -> dict:
        return {
            "power_w": 1200.0,
            "energy_kwh": 0.0,
            "voltage_v": 230.0,
            "current_a": 5.22,
            "power_factor": 0.95,
            "overload": False,
        }

    def _init_ev_charger(self) -> dict:
        return {
            "charging": False,
            "power_kw": 0.0,
            "energy_kwh": 0.0,
            "vehicle_soc_pct": None,
            "vehicle_connected": False,
        }

    def _init_solar_panel(self) -> dict:
        return {
            "current_power_w": 0.0,
            "daily_energy_kwh": 0.0,
            "total_energy_kwh": 0.0,
            "panel_temp_c": 25.0,
            "fault": False,
        }

    def _init_button_device(self) -> dict:
        return {"last_event": None, "last_event_time": None}

    # ------------------------------------------------------------------
    # HA coordinator interface
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        new_state = dict(self.data) if self.data else self._build_initial_state()
        interval_s: float = self.update_interval.total_seconds()

        if self.random_availability:
            if new_state.get("connected", True):
                if random.random() < 0.01:
                    new_state["connected"] = False
            else:
                if random.random() < 0.25:
                    new_state["connected"] = True

        if not new_state.get("connected", True):
            return new_state

        # Battery drain — robot vacuum handled inside its own updater
        drain_rate = BATTERY_DRAIN_RATES.get(self.device_type)
        if drain_rate is not None and "battery" in new_state and self.device_type != DEVICE_TYPE_ROBOT_VACUUM:
            drain = drain_rate * interval_s * 100
            if self.device_type == DEVICE_TYPE_SIREN and new_state.get("is_on"):
                drain *= 10
            new_state["battery"] = max(0.0, round(new_state["battery"] - drain, 4))
            if self.device_type == DEVICE_TYPE_SMOKE_CO_DETECTOR:
                new_state["battery_low"] = new_state["battery"] < 20
            if self.device_type == DEVICE_TYPE_WATER_LEAK:
                new_state["battery_low"] = new_state["battery"] < 20

        if self.random_updates:
            updaters = {
                DEVICE_TYPE_SMART_LIGHT: self._update_smart_light,
                DEVICE_TYPE_SMART_PLUG: self._update_smart_plug,
                DEVICE_TYPE_WEATHER_STATION: self._update_weather_station,
                DEVICE_TYPE_GARAGE_DOOR: self._update_garage_door,
                DEVICE_TYPE_THERMOSTAT: self._update_thermostat,
                DEVICE_TYPE_HUMIDIFIER: self._update_humidifier,
                DEVICE_TYPE_SMART_LOCK: self._update_smart_lock,
                DEVICE_TYPE_MOTION_SENSOR: self._update_motion_sensor,
                DEVICE_TYPE_DOOR_WINDOW_SENSOR: self._update_door_window,
                DEVICE_TYPE_SMOKE_CO_DETECTOR: self._update_smoke_co,
                DEVICE_TYPE_ALARM_PANEL: self._update_alarm_panel,
                DEVICE_TYPE_SIREN: self._update_siren,
                DEVICE_TYPE_WATER_LEAK: self._update_water_leak,
                DEVICE_TYPE_DOORBELL: self._update_doorbell,
                DEVICE_TYPE_MEDIA_PLAYER: self._update_media_player,
                DEVICE_TYPE_SMART_FAN: self._update_smart_fan,
                DEVICE_TYPE_AIR_QUALITY: self._update_air_quality,
                DEVICE_TYPE_ROBOT_VACUUM: self._update_robot_vacuum,
                DEVICE_TYPE_SMART_BLIND: self._update_smart_blind,
                DEVICE_TYPE_SMART_VALVE: self._update_smart_valve,
                DEVICE_TYPE_ENERGY_METER: self._update_energy_meter,
                DEVICE_TYPE_EV_CHARGER: self._update_ev_charger,
                DEVICE_TYPE_SOLAR_PANEL: self._update_solar_panel,
                DEVICE_TYPE_BUTTON_DEVICE: self._update_button_device,
            }
            updater = updaters.get(self.device_type)
            if updater:
                updater(new_state, interval_s)

        return new_state

    async def async_config_entry_first_refresh(self) -> None:
        self.async_set_updated_data(self._build_initial_state())

    def set_state(self, **kwargs: Any) -> None:
        """Apply state overrides immediately."""
        new_state = dict(self.data) if self.data else {}
        new_state.update(kwargs)
        self.async_set_updated_data(new_state)

    # ------------------------------------------------------------------
    # Update methods
    # ------------------------------------------------------------------

    def _update_smart_light(self, s: dict, interval_s: float) -> None:
        if random.random() < self._light_on_probability():
            s["is_on"] = not s["is_on"]
        if s["is_on"]:
            s["brightness"] = max(1, min(255, s["brightness"] + random.randint(-20, 20)))
            s["color_temp_kelvin"] = max(2000, min(6500, s["color_temp_kelvin"] + random.randint(-100, 100)))
            h, sat = s["hs_color"]
            h = round((h + random.uniform(-5, 5)) % 360, 1)
            sat = round(max(0.0, min(100.0, sat + random.uniform(-3, 3))), 1)
            s["hs_color"] = [h, sat]
            if random.random() < 0.02:
                s["effect"] = random.choice(["none", "colorloop", "flash", "random"])

    def _update_smart_plug(self, s: dict, interval_s: float) -> None:
        if random.random() < 0.05:
            s["is_on"] = not s["is_on"]
        if s["is_on"]:
            s["power_w"] = round(random.uniform(20, 600), 1)
            s["energy_kwh"] = round(s["energy_kwh"] + s["power_w"] * interval_s / 3_600_000, 6)
        else:
            s["power_w"] = 0.0

    def _update_weather_station(self, s: dict, interval_s: float) -> None:
        s["temperature_c"] = round(
            max(-20.0, min(50.0, s["temperature_c"] + random.uniform(-0.3, 0.3))), 1
        )
        s["humidity_pct"] = round(
            max(0.0, min(100.0, s["humidity_pct"] + random.uniform(-1.5, 1.5))), 1
        )

    def _update_garage_door(self, s: dict, interval_s: float) -> None:
        if random.random() < 0.02:
            s["is_open"] = not s["is_open"]
            s["position"] = 100 if s["is_open"] else 0
        if random.random() < 0.02:
            s["obstruction"] = not s["obstruction"]

    def _update_thermostat(self, s: dict, interval_s: float) -> None:
        target = self._comfort_temp() if self.simulation_profile != SIM_PROFILE_RANDOM else s["target_temp"]
        diff = target - s["current_temp"]
        s["current_temp"] = round(s["current_temp"] + diff * 0.05 + random.uniform(-0.1, 0.1), 1)
        s["current_humidity"] = round(
            max(20.0, min(80.0, s["current_humidity"] + random.uniform(-0.5, 0.5))), 1
        )
        if s["hvac_mode"] == "off":
            s["hvac_action"] = "off"
        elif s["hvac_mode"] in ("heat", "heat_cool") and s["current_temp"] < s["target_temp"] - 0.5:
            s["hvac_action"] = "heating"
        elif s["hvac_mode"] in ("cool", "heat_cool") and s["current_temp"] > s["target_temp"] + 0.5:
            s["hvac_action"] = "cooling"
        else:
            s["hvac_action"] = "idle"
        if random.random() < 0.01:
            s["hvac_mode"] = random.choice(["heat", "cool", "heat_cool", "off"])
        if random.random() < 0.03:
            s["fan_mode"] = random.choice(["auto", "low", "medium", "high"])
        if random.random() < 0.02:
            s["swing_mode"] = random.choice(["off", "vertical", "horizontal", "both"])

    def _update_humidifier(self, s: dict, interval_s: float) -> None:
        if random.random() < 0.05:
            s["is_on"] = not s["is_on"]
        if s["is_on"]:
            diff = s["target_humidity"] - s["current_humidity"]
            s["current_humidity"] = round(
                max(20.0, min(100.0, s["current_humidity"] + diff * 0.03 + random.uniform(-0.3, 0.3))), 1
            )
            s["water_level_pct"] = round(max(0.0, s["water_level_pct"] - 0.01 * interval_s / 60), 3)
        else:
            s["current_humidity"] = round(
                max(20.0, min(100.0, s["current_humidity"] + random.uniform(-0.3, 0.0))), 1
            )
        if random.random() < 0.03:
            s["mode"] = random.choice(["auto", "sleep", "baby"])

    def _update_smart_lock(self, s: dict, interval_s: float) -> None:
        if s["lock_state"] == "locking":
            s["lock_state"] = "locked"
        elif s["lock_state"] == "unlocking":
            s["lock_state"] = "unlocked"
        elif random.random() < 0.01:
            if s["lock_state"] == "locked":
                s["lock_state"] = "unlocking"
            elif s["lock_state"] == "unlocked":
                s["lock_state"] = "locking"
        if random.random() < 0.02:
            s["door_contact"] = not s["door_contact"]
        if s["lock_state"] not in ("jammed",) and random.random() < 0.005:
            s["lock_state"] = "jammed"
        elif s["lock_state"] == "jammed" and random.random() < 0.5:
            s["lock_state"] = "locked"

    def _update_motion_sensor(self, s: dict, interval_s: float) -> None:
        if not s["motion"]:
            if random.random() < self._motion_probability():
                s["motion"] = True
        else:
            if random.random() < 0.60:
                s["motion"] = False
        if not s["tamper"]:
            if random.random() < 0.002:
                s["tamper"] = True
        else:
            s["tamper"] = False
        s["illuminance_lx"] = round(
            max(0.0, min(2000.0, s["illuminance_lx"] + random.uniform(-10, 10))), 1
        )

    def _update_door_window(self, s: dict, interval_s: float) -> None:
        if random.random() < 0.02:
            s["contact"] = not s["contact"]
        if not s["tamper"]:
            if random.random() < 0.002:
                s["tamper"] = True
        else:
            s["tamper"] = False
        s["temperature_c"] = round(
            max(-10.0, min(40.0, s["temperature_c"] + random.uniform(-0.2, 0.2))), 1
        )

    def _update_smoke_co(self, s: dict, interval_s: float) -> None:
        if not s["smoke"]:
            if random.random() < 0.001:
                s["smoke"] = True
        else:
            if random.random() < 0.5:
                s["smoke"] = False
        if not s["carbon_monoxide"]:
            if random.random() < 0.001:
                s["carbon_monoxide"] = True
        else:
            if random.random() < 0.5:
                s["carbon_monoxide"] = False
        if s["carbon_monoxide"]:
            s["co_ppm"] = round(min(100.0, s["co_ppm"] + random.uniform(0, 5)), 1)
        else:
            s["co_ppm"] = round(max(0.0, s["co_ppm"] - random.uniform(0, 3)), 1)

    def _update_alarm_panel(self, s: dict, interval_s: float) -> None:
        state = s["alarm_state"]
        if state == "triggered":
            self._alarm_trigger_count += 1
            if self._alarm_trigger_count >= 3:
                s["alarm_state"] = "disarmed"
                self._alarm_trigger_count = 0
        elif state == "disarmed":
            if random.random() < 0.02:
                s["alarm_state"] = random.choice(["armed_away", "armed_home"])
        elif state in ("armed_away", "armed_home", "armed_night"):
            if random.random() < 0.005:
                s["alarm_state"] = "triggered"
                self._alarm_trigger_count = 0

    def _update_siren(self, s: dict, interval_s: float) -> None:
        if random.random() < 0.05:
            s["is_on"] = not s["is_on"]
        if s["is_on"] and random.random() < 0.10:
            s["tone"] = random.choice(["default", "fire", "burglar", "medical"])

    def _update_water_leak(self, s: dict, interval_s: float) -> None:
        if not s["moisture"]:
            if random.random() < 0.01:
                s["moisture"] = True
        else:
            if random.random() < 0.30:
                s["moisture"] = False
        s["temperature_c"] = round(
            max(-5.0, min(40.0, s["temperature_c"] + random.uniform(-0.2, 0.2))), 1
        )

    def _update_doorbell(self, s: dict, interval_s: float) -> None:
        if not s["motion"]:
            if random.random() < self._motion_probability():
                s["motion"] = True
        else:
            if random.random() < 0.6:
                s["motion"] = False
        if random.random() < 0.01:
            s["last_press_time"] = dt_util.utcnow().isoformat()

    def _update_media_player(self, s: dict, interval_s: float) -> None:
        state = s["state"]
        r = random.random()
        if state == "idle":
            if r < 0.03:
                track = random.choice(_MEDIA_TRACKS)
                s["state"] = "playing"
                s["media_artist"] = track[0]
                s["media_album_name"] = track[1]
                s["media_title"] = track[2]
                s["media_duration"] = random.randint(120, 360)
                s["media_position"] = 0
        elif state == "playing":
            if r < 0.02:
                s["state"] = "paused"
            elif r < 0.04:
                s["state"] = "idle"
                s["media_title"] = None
                s["media_artist"] = None
                s["media_album_name"] = None
                s["media_duration"] = None
                s["media_position"] = 0
            else:
                s["volume_level"] = round(
                    max(0.0, min(1.0, s["volume_level"] + random.uniform(-0.02, 0.02))), 2
                )
                s["media_position"] = min(
                    s.get("media_duration") or 360,
                    s["media_position"] + int(interval_s),
                )
                # Next track
                if s["media_position"] >= (s.get("media_duration") or 360):
                    track = random.choice(_MEDIA_TRACKS)
                    s["media_artist"] = track[0]
                    s["media_album_name"] = track[1]
                    s["media_title"] = track[2]
                    s["media_duration"] = random.randint(120, 360)
                    s["media_position"] = 0
        elif state == "paused":
            if r < 0.05:
                s["state"] = "playing"
        if random.random() < 0.05:
            s["source"] = random.choice(s["source_list"])
        if random.random() < 0.02:
            s["shuffle"] = not s["shuffle"]
        if random.random() < 0.02:
            s["repeat"] = random.choice(["off", "one", "all"])
        if random.random() < 0.03:
            s["sound_mode"] = random.choice(s["sound_mode_list"])

    def _update_smart_fan(self, s: dict, interval_s: float) -> None:
        if random.random() < 0.05:
            s["is_on"] = not s["is_on"]
        if s["is_on"]:
            if random.random() < 0.10:
                s["oscillating"] = not s["oscillating"]
            if random.random() < 0.05:
                s["preset_mode"] = random.choice(["normal", "sleep", "turbo"])
            if random.random() < 0.02:
                s["direction"] = "reverse" if s["direction"] == "forward" else "forward"
            s["percentage"] = max(1, min(100, s["percentage"] + random.randint(-5, 5)))

    def _update_air_quality(self, s: dict, interval_s: float) -> None:
        s["pm25_ugm3"] = round(max(0.0, min(150.0, s["pm25_ugm3"] + random.uniform(-1, 1))), 1)
        s["pm10_ugm3"] = round(max(0.0, min(200.0, s["pm10_ugm3"] + random.uniform(-2, 2))), 1)
        s["co2_ppm"] = round(max(400.0, min(2000.0, s["co2_ppm"] + random.uniform(-10, 10))), 1)
        s["voc_index"] = max(0, min(500, s["voc_index"] + random.randint(-5, 5)))
        s["aqi"] = min(500, int(s["pm25_ugm3"] * 4.0 / 3.0))
        s["temperature_c"] = round(
            max(10.0, min(40.0, s["temperature_c"] + random.uniform(-0.1, 0.1))), 1
        )
        s["humidity_pct"] = round(
            max(0.0, min(100.0, s["humidity_pct"] + random.uniform(-0.5, 0.5))), 1
        )

    def _update_robot_vacuum(self, s: dict, interval_s: float) -> None:
        self._vacuum_tick += 1
        status = s["status"]
        if status == "docked":
            s["battery"] = min(100.0, s["battery"] + 0.8 * interval_s / 60)
            if s["battery"] >= 100.0 and random.random() < 0.05:
                s["status"] = "cleaning"
                self._vacuum_tick = 0
        elif status == "cleaning":
            s["battery"] = max(0.0, s["battery"] - 1.0 * interval_s / 60)
            s["cleaned_area_m2"] = round(s["cleaned_area_m2"] + 0.1, 2)
            if s["battery"] < 20 or (self._vacuum_tick > 30 and random.random() < 0.02):
                s["status"] = "returning"
            if random.random() < 0.01:
                s["status"] = "error"
        elif status == "returning":
            s["battery"] = max(0.0, s["battery"] - 0.3 * interval_s / 60)
            if random.random() < 0.15:
                s["status"] = "docked"
        elif status == "error":
            if random.random() < 0.20:
                s["status"] = "docked"

    def _update_smart_blind(self, s: dict, interval_s: float) -> None:
        if random.random() < 0.03:
            s["position"] = max(0, min(100, s["position"] + random.randint(-25, 25)))
            s["is_closed"] = s["position"] == 0
        if random.random() < 0.05:
            s["tilt_position"] = max(0, min(100, s["tilt_position"] + random.randint(-10, 10)))

    def _update_smart_valve(self, s: dict, interval_s: float) -> None:
        if random.random() < 0.03:
            s["is_open"] = not s["is_open"]
        if s["is_open"]:
            s["flow_rate_lpm"] = round(random.uniform(1.5, 8.0), 2)
            s["volume_l"] = round(s["volume_l"] + s["flow_rate_lpm"] * interval_s / 60, 3)
        else:
            s["flow_rate_lpm"] = 0.0
        if not s["leak_detected"]:
            if random.random() < 0.005:
                s["leak_detected"] = True
        else:
            s["leak_detected"] = False

    def _update_energy_meter(self, s: dict, interval_s: float) -> None:
        s["power_w"] = round(max(0.0, min(5000.0, s["power_w"] + random.uniform(-50, 50))), 1)
        s["voltage_v"] = round(max(210.0, min(250.0, s["voltage_v"] + random.uniform(-0.5, 0.5))), 1)
        s["power_factor"] = round(max(0.7, min(1.0, s["power_factor"] + random.uniform(-0.01, 0.01))), 3)
        s["current_a"] = round(s["power_w"] / s["voltage_v"], 2) if s["voltage_v"] else 0.0
        s["energy_kwh"] = round(s["energy_kwh"] + s["power_w"] * interval_s / 3_600_000, 6)
        s["overload"] = s["power_w"] > 4500

    def _update_ev_charger(self, s: dict, interval_s: float) -> None:
        if random.random() < 0.03:
            s["vehicle_connected"] = not s["vehicle_connected"]
            if not s["vehicle_connected"]:
                s["vehicle_soc_pct"] = None
                s["charging"] = False
                s["power_kw"] = 0.0
            else:
                s["vehicle_soc_pct"] = round(random.uniform(10, 80), 1)
        if s["vehicle_connected"] and s["charging"]:
            soc = s.get("vehicle_soc_pct") or 0.0
            if soc >= 100.0:
                s["charging"] = False
                s["power_kw"] = 0.0
            else:
                s["power_kw"] = round(random.uniform(7.2, 11.0), 2)
                charge_added = s["power_kw"] * interval_s / 3600 * 100 / 60
                s["vehicle_soc_pct"] = min(100.0, round(soc + charge_added, 1))
                s["energy_kwh"] = round(s["energy_kwh"] + s["power_kw"] * interval_s / 3600, 4)
        elif not s["vehicle_connected"]:
            s["power_kw"] = 0.0

    def _update_solar_panel(self, s: dict, interval_s: float) -> None:
        now = dt_util.now()
        hour_frac = now.hour + now.minute / 60.0
        # 0 at 6am, π at 6pm
        solar_angle = math.pi * (hour_frac - 6) / 12
        base_power = max(0.0, math.sin(solar_angle)) * 4000.0
        s["current_power_w"] = round(base_power * random.uniform(0.9, 1.1), 1)
        s["panel_temp_c"] = round(25.0 + s["current_power_w"] / 100, 1)
        kwh_step = s["current_power_w"] * interval_s / 3_600_000
        s["daily_energy_kwh"] = round(s["daily_energy_kwh"] + kwh_step, 4)
        s["total_energy_kwh"] = round(s["total_energy_kwh"] + kwh_step, 4)
        if now.hour == 0 and now.minute == 0:
            s["daily_energy_kwh"] = 0.0
        if not s["fault"]:
            if random.random() < 0.002:
                s["fault"] = True
        else:
            s["fault"] = False

    def _update_button_device(self, s: dict, interval_s: float) -> None:
        if random.random() < 0.02:
            s["last_event"] = random.choice(["single_press", "double_press", "long_press"])
            s["last_event_time"] = dt_util.utcnow().isoformat()
