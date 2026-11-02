# Simulated Devices — Home Assistant Custom Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-2.2.0-blue)
![HA Version](https://img.shields.io/badge/HA-2026.5%2B-green)

Simulate virtual smart home devices in Home Assistant for testing automations, dashboards, and integrations — without needing real hardware.

---

## Features

- **33 device types** across 33 HA entity platforms
- **"Everything" device** — one device carrying an instance of every entity type at once
- **Parent/child devices** — power strip, dual-lens camera and 2-gang wall switch split across sub-devices (HA 2026.12+)
- **Realistic simulation** — state changes, battery drain, sensor drift
- **Simulation profiles** — Random, Home, Away, Night
- **One-click batch create** — spin up all 33 devices at once
- **Dashboard generator** — auto-builds a Lovelace dashboard from your devices
- **5 services** — force state, inject faults, trigger events, reset battery, set profile
- **Fault injection** — instantly trigger smoke, CO, leak, motion, overload, offline with auto-clear
- **HA Diagnostics** support

---

## Device Types

| Category | Devices |
|---|---|
| **Lighting** | Smart Light (brightness, color temp, HS color, effects) |
| **Climate** | Thermostat (HVAC modes, fan/swing, presets), Humidifier |
| **Security** | Smart Lock, Motion Sensor, Door/Window Sensor, Smoke/CO Detector, Alarm Panel, Siren, Water Leak, Doorbell |
| **Entertainment** | Media Player (artist, album, shuffle, repeat, sound mode) |
| **Comfort** | Smart Fan (speed, oscillation, direction), Air Quality Sensor |
| **Appliances** | Robot Vacuum, Smart Blind (with tilt), Smart Valve |
| **Energy** | Energy Meter, EV Charger, Solar Panel, Smart Plug |
| **Input** | Button Device |
| **Infrastructure** | Garage Door |
| **Vision** | Security Camera (generated video stills + snapshot image) |
| **Water/Outdoor** | Water Heater, Lawn Mower |
| **Presence** | Phone Tracker (device_tracker with GPS drift) |
| **Controller** | Home Hub (number, select, text, date, datetime, time, todo, calendar, notify, remote, scenes) |
| **Parent/child** | Power Strip, Dual-Lens Camera, 2-Gang Wall Switch, Child Device Test Rig |
| **Composite** | **Everything** — one device with all of the above |

### The "Everything" device

Pick **Everything (all entity types)** in *Add single device* to get a single HA
device that owns an instance of every entity type this integration can produce —
132 entities spanning all 33 platforms, on one device page.

Internally it runs one coordinator per sub-type, so each sub-device keeps its own
independent state (the light's `is_on` is not the siren's `is_on`). Entity names
are prefixed with the sub-type, e.g. `Smart Light Light`, `Robot Vacuum Battery`.

It is excluded from **Create all device types at once** — that batch creates the
33 real types as separate devices.

The parent/child types below are left out of the **Everything** device: a child
device cannot itself be a child, so they cannot be folded into one device. They
*are* part of the batch.

### Parent/child (sub-)device types

Four types exercise the parent/child device relationship core added in 2026.12.
The integration registers the parent device first, then gives each child entity a
`ChildDeviceInfo` pointing at the parent's device registry id. A child uses the
parent's config entry, has no connections or firmware of its own, inherits the
parent's area, and cannot be a parent itself.

| Type | Parent entities | Child devices |
|---|---|---|
| **Power Strip** | Connected, Wi-Fi signal, Firmware, Total power | Outlet 1–4, each with Switch, Power (W) and Energy (kWh); Outlet 4 also has an Overload sensor |
| **Dual-Lens Camera** | Connected, Wi-Fi signal, Firmware, Privacy mode | Wide lens, Telephoto lens — each a Camera plus Motion |
| **2-Gang Wall Switch** | Connected, Wi-Fi signal, Firmware (diagnostics only) | Left, Right — each a Light |
| **Child Device Test Rig** | *none* | Four edge cases, below |

Outlet power follows the switch, and energy accumulates from it, so the outlets
react even with **Random state changes** turned off. Privacy mode blanks both
lenses.

The **Child Device Test Rig** is there to break frontend layouts on purpose:

- **Normal child** — one Switch, for contrast with the rest
- **Diagnostics only** — a diagnostic Fault sensor and a config Setpoint, so it
  must *not* appear in the parent's Controls or Sensors cards
- **Disabled by default** — registered with `disabled_by=INTEGRATION`; enable it
  from the device page to see it appear
- *(unnamed child)* — registered with no name at all, to check empty headings
- The rig's **parent has no entities of its own**, only children

These four types need HA 2026.12 or newer. On an older core their config entries
fail to set up with a clear error; every other device type keeps working.

---

## Installation

### Via HACS (recommended)

[![Open your Home Assistant instance and add a custom repository.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=marcinbauer-ohf&repository=simulated-devices&category=integration)

Or manually:

1. Open HACS → **Integrations**
2. Click the three-dot menu (⋮) → **Custom repositories**
3. Add your repo URL, category **Integration** → click **Add**
4. Search for **Simulated Devices** → **Download**
5. Restart Home Assistant

### Manual

1. Copy the `simulated_devices` folder to `<config>/custom_components/`
2. Restart Home Assistant

---

## Setup

1. **Settings → Devices & Services → Add device**
2. Search for **Simulated Devices**
3. Choose an option:
   - **Add single device** — pick a device type, give it a name
   - **Create all device types at once** — set a name prefix (e.g. `Sim`) and create all 33 in one step
   - **Generate dashboard** — build or rebuild the Lovelace dashboard
   - **Remove all devices** — remove everything (with confirmation)

---

## Configuration

Each device has configurable options (accessible via Settings → Devices & Services → device → Configure):

| Option | Default | Description |
|---|---|---|
| Update interval | 10s | How often state changes are simulated |
| Random state changes | On | Toggle simulation on/off |
| Random availability | Off | Simulate random connectivity drops |
| Simulation profile | Random | Behavioral pattern (see below) |

### Simulation Profiles

| Profile | Behavior |
|---|---|
| **Random** | Pure random state changes (default) |
| **Home** | Occupied daytime — more motion, lights on in evenings |
| **Away** | Unoccupied — minimal activity |
| **Night** | Sleeping — low motion, dimmed/off lights, cooler temps |

---

## Services

All services are available under **Developer Tools → Services**.

| Service | Description |
|---|---|
| `simulated_devices.reset_battery` | Reset battery to 100% |
| `simulated_devices.force_state` | Override any state key directly |
| `simulated_devices.trigger_event` | Fire a button press or doorbell event |
| `simulated_devices.set_profile` | Change simulation profile at runtime |
| `simulated_devices.inject_fault` | Trigger a fault condition with auto-clear |
| `simulated_devices.generate_dashboard` | Regenerate the Lovelace dashboard |

### Fault Types (inject_fault)

`smoke_alarm` · `co_alarm` · `leak` · `motion` · `tamper` · `overload` · `battery_critical` · `offline`

Each fault auto-clears after a configurable duration (default 30s).

---

## Dashboard

The dashboard generator creates a Lovelace **sections layout** dashboard at `/simulated-devices` with one section per device containing appropriate cards:

- Thermostat → `thermostat` card
- Media Player → `media-control` card
- Alarm Panel → `alarm-panel` card
- Everything else → `tile` cards

A **Regenerate Dashboard** button is included at the top of the dashboard so you can refresh it after adding more devices.

---

## License

MIT
