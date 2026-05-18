"""Constants for the simulated_devices integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "simulated_devices"

CONF_DEVICE_TYPE = "device_type"
CONF_RANDOM_AVAILABILITY = "random_availability"
CONF_RANDOM_UPDATES = "random_updates"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_SIMULATION_PROFILE = "simulation_profile"

ZEROCONF_SERVICE_TYPE = "_simulated-device._tcp.local."
ZEROCONF_PROP_DEVICE_TYPE = "device_type"
ZEROCONF_PROP_UNIQUE_ID = "unique_id"
ZEROCONF_PROP_NAME = "name"

DEFAULT_DEVICE_NAME = "Simulated Device"
DEFAULT_UPDATE_INTERVAL = 10
DEFAULT_RANDOM_UPDATES = True
DEFAULT_RANDOM_AVAILABILITY = False
DEFAULT_SIMULATION_PROFILE = "random"

# --- Device type constants ---

# Existing
DEVICE_TYPE_SMART_LIGHT = "smart_light"
DEVICE_TYPE_SMART_PLUG = "smart_plug"
DEVICE_TYPE_WEATHER_STATION = "weather_station"
DEVICE_TYPE_GARAGE_DOOR = "garage_door"

# Climate/HVAC
DEVICE_TYPE_THERMOSTAT = "thermostat"
DEVICE_TYPE_HUMIDIFIER = "humidifier"

# Security
DEVICE_TYPE_SMART_LOCK = "smart_lock"
DEVICE_TYPE_MOTION_SENSOR = "motion_sensor"
DEVICE_TYPE_DOOR_WINDOW_SENSOR = "door_window_sensor"
DEVICE_TYPE_SMOKE_CO_DETECTOR = "smoke_co_detector"
DEVICE_TYPE_ALARM_PANEL = "alarm_panel"
DEVICE_TYPE_SIREN = "siren"
DEVICE_TYPE_WATER_LEAK = "water_leak"
DEVICE_TYPE_DOORBELL = "doorbell"

# AV/Entertainment
DEVICE_TYPE_MEDIA_PLAYER = "media_player"

# Comfort/Environment
DEVICE_TYPE_SMART_FAN = "smart_fan"
DEVICE_TYPE_AIR_QUALITY = "air_quality"

# Appliances/Automation
DEVICE_TYPE_ROBOT_VACUUM = "robot_vacuum"
DEVICE_TYPE_SMART_BLIND = "smart_blind"
DEVICE_TYPE_SMART_VALVE = "smart_valve"

# Energy/Infrastructure
DEVICE_TYPE_ENERGY_METER = "energy_meter"
DEVICE_TYPE_EV_CHARGER = "ev_charger"
DEVICE_TYPE_SOLAR_PANEL = "solar_panel"

# Input
DEVICE_TYPE_BUTTON_DEVICE = "button_device"

DEVICE_TYPES: dict[str, str] = {
    # Existing
    DEVICE_TYPE_SMART_LIGHT: "Smart Light",
    DEVICE_TYPE_SMART_PLUG: "Smart Plug",
    DEVICE_TYPE_WEATHER_STATION: "Weather Station",
    DEVICE_TYPE_GARAGE_DOOR: "Garage Door",
    # Climate
    DEVICE_TYPE_THERMOSTAT: "Thermostat",
    DEVICE_TYPE_HUMIDIFIER: "Humidifier",
    # Security
    DEVICE_TYPE_SMART_LOCK: "Smart Lock",
    DEVICE_TYPE_MOTION_SENSOR: "Motion Sensor",
    DEVICE_TYPE_DOOR_WINDOW_SENSOR: "Door/Window Sensor",
    DEVICE_TYPE_SMOKE_CO_DETECTOR: "Smoke/CO Detector",
    DEVICE_TYPE_ALARM_PANEL: "Alarm Panel",
    DEVICE_TYPE_SIREN: "Siren",
    DEVICE_TYPE_WATER_LEAK: "Water Leak Sensor",
    DEVICE_TYPE_DOORBELL: "Doorbell",
    # AV
    DEVICE_TYPE_MEDIA_PLAYER: "Media Player",
    # Comfort
    DEVICE_TYPE_SMART_FAN: "Smart Fan",
    DEVICE_TYPE_AIR_QUALITY: "Air Quality Sensor",
    # Appliances
    DEVICE_TYPE_ROBOT_VACUUM: "Robot Vacuum",
    DEVICE_TYPE_SMART_BLIND: "Smart Blind",
    DEVICE_TYPE_SMART_VALVE: "Smart Valve",
    # Energy
    DEVICE_TYPE_ENERGY_METER: "Energy Meter",
    DEVICE_TYPE_EV_CHARGER: "EV Charger",
    DEVICE_TYPE_SOLAR_PANEL: "Solar Panel",
    # Input
    DEVICE_TYPE_BUTTON_DEVICE: "Button Device",
}

PLATFORMS: tuple[Platform, ...] = (
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.COVER,
    Platform.EVENT,
    Platform.FAN,
    Platform.HUMIDIFIER,
    Platform.LIGHT,
    Platform.LOCK,
    Platform.MEDIA_PLAYER,
    Platform.SENSOR,
    Platform.SIREN,
    Platform.SWITCH,
    Platform.VACUUM,
    Platform.VALVE,
)

MIN_UPDATE_INTERVAL = 1
MAX_UPDATE_INTERVAL = 3600

# Battery drain rates per update tick (% per interval second, scaled by interval)
# None = mains powered, skip battery entirely
BATTERY_DRAIN_RATES: dict[str, float | None] = {
    DEVICE_TYPE_SMART_LIGHT: 0.05 / 3600,
    DEVICE_TYPE_SMART_PLUG: None,
    DEVICE_TYPE_WEATHER_STATION: 0.05 / 3600,
    DEVICE_TYPE_GARAGE_DOOR: 0.05 / 3600,
    DEVICE_TYPE_THERMOSTAT: None,
    DEVICE_TYPE_HUMIDIFIER: None,
    DEVICE_TYPE_SMART_LOCK: 0.003 / 3600,
    DEVICE_TYPE_MOTION_SENSOR: 0.002 / 3600,
    DEVICE_TYPE_DOOR_WINDOW_SENSOR: 0.001 / 3600,
    DEVICE_TYPE_SMOKE_CO_DETECTOR: 0.002 / 3600,
    DEVICE_TYPE_ALARM_PANEL: None,
    DEVICE_TYPE_SIREN: 0.05 / 3600,
    DEVICE_TYPE_WATER_LEAK: 0.001 / 3600,
    DEVICE_TYPE_DOORBELL: 0.002 / 3600,
    DEVICE_TYPE_MEDIA_PLAYER: None,
    DEVICE_TYPE_SMART_FAN: None,
    DEVICE_TYPE_AIR_QUALITY: None,
    DEVICE_TYPE_ROBOT_VACUUM: None,  # handled specially in coordinator
    DEVICE_TYPE_SMART_BLIND: 0.002 / 3600,
    DEVICE_TYPE_SMART_VALVE: None,
    DEVICE_TYPE_ENERGY_METER: None,
    DEVICE_TYPE_EV_CHARGER: None,
    DEVICE_TYPE_SOLAR_PANEL: None,
    DEVICE_TYPE_BUTTON_DEVICE: 0.001 / 3600,
}

# Simulation profile constants
SIM_PROFILE_RANDOM = "random"
SIM_PROFILE_HOME = "home"
SIM_PROFILE_AWAY = "away"
SIM_PROFILE_NIGHT = "night"

SIMULATION_PROFILES: dict[str, str] = {
    SIM_PROFILE_RANDOM: "Random",
    SIM_PROFILE_HOME: "Home",
    SIM_PROFILE_AWAY: "Away",
    SIM_PROFILE_NIGHT: "Night",
}

# Service names
SERVICE_RESET_BATTERY = "reset_battery"
SERVICE_FORCE_STATE = "force_state"
SERVICE_TRIGGER_EVENT = "trigger_event"
SERVICE_SET_PROFILE = "set_profile"
SERVICE_INJECT_FAULT = "inject_fault"
SERVICE_GENERATE_DASHBOARD = "generate_dashboard"

FAULT_TYPES = {
    "smoke_alarm": {"smoke": True},
    "co_alarm": {"carbon_monoxide": True},
    "leak": {"moisture": True, "leak_detected": True},
    "motion": {"motion": True},
    "tamper": {"tamper": True},
    "overload": {"overload": True},
    "battery_critical": {"battery": 5.0},
    "offline": {"connected": False},
}
