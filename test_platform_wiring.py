"""Wiring checks — run with `python3 test_platform_wiring.py`.

Mostly these parse the source instead of importing it, so they run without Home
Assistant installed. They catch the mistakes this integration is actually
prone to: a platform listed in PLATFORMS with no module behind it, or a device
type that no coordinator builder knows how to create state for.

demo_outlets() is the exception: it imports the coordinator behind stub
Home Assistant modules to run the one piece of real arithmetic here, the power
strip's per-outlet power and energy.
"""

from __future__ import annotations

import ast
import pathlib
import sys
import types

HERE = pathlib.Path(__file__).parent


def _tree(name: str) -> ast.Module:
    return ast.parse((HERE / name).read_text())


def _device_type_constants(const_tree: ast.Module) -> dict[str, str]:
    """Map DEVICE_TYPE_FOO -> "foo" for every module-level assignment."""
    out = {}
    for node in const_tree.body:
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id.startswith("DEVICE_TYPE_")
            and isinstance(node.value, ast.Constant)
        ):
            out[node.targets[0].id] = node.value.value
    return out


def _dict_keys(tree: ast.Module, variable: str) -> set[str]:
    """Names used as keys of a module-level dict literal."""
    for node in tree.body:
        if (
            isinstance(node, (ast.Assign, ast.AnnAssign))
            and isinstance(target := getattr(node, "target", None) or node.targets[0], ast.Name)
            and target.id == variable
            and isinstance(node.value, ast.Dict)
        ):
            return {k.id for k in node.value.keys if isinstance(k, ast.Name)}
    raise AssertionError(f"{variable} not found as a dict literal")


def _nested_dict_keys(tree: ast.Module, func: str) -> list[set[str]]:
    """Keys of every dict literal assigned inside a function body."""
    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func:
            for inner in ast.walk(node):
                if isinstance(inner, ast.Dict) and inner.keys and all(
                    isinstance(k, ast.Name) for k in inner.keys
                ):
                    found.append({k.id for k in inner.keys})
    return found


def _dispatch_targets(tree: ast.Module, func: str) -> set[str]:
    """Method names on the right-hand side of a dispatch dict (self._foo)."""
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func:
            for inner in ast.walk(node):
                if isinstance(inner, ast.Dict):
                    out |= {
                        v.attr
                        for v in inner.values
                        if isinstance(v, ast.Attribute)
                        and isinstance(v.value, ast.Name)
                        and v.value.id == "self"
                    }
    return out


def _set_literal_names(tree: ast.Module, variable: str) -> set[str]:
    """Names inside a module-level set literal, bare or wrapped in frozenset()."""
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(
            target := getattr(node, "target", None) or node.targets[0], ast.Name
        ):
            if target.id != variable:
                continue
            for inner in ast.walk(node):
                if isinstance(inner, ast.Set):
                    return {e.id for e in inner.elts if isinstance(e, ast.Name)}
    raise AssertionError(f"{variable} not found as a set literal")


def demo() -> None:
    const = _tree("const.py")
    coordinator = _tree("coordinator.py")
    child_devices = _tree("child_devices.py")
    constants = _device_type_constants(const)

    declared = _dict_keys(const, "DEVICE_TYPES")
    assert declared <= set(constants), declared - set(constants)

    # Every platform in PLATFORMS must have a module next to it.
    platforms = [
        node.attr
        for node in ast.walk(const)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "Platform"
    ]
    assert platforms, "no Platform.* entries found in const.py"
    for platform in platforms:
        module = HERE / f"{platform.lower()}.py"
        assert module.exists(), f"PLATFORMS lists {platform} but {module.name} is missing"

    # Battery table must cover every declared type, or the coordinator's
    # .get() silently makes a device mains-powered.
    assert _dict_keys(const, "BATTERY_DRAIN_RATES") == declared

    # Every real type needs an initial-state builder; "everything" is the
    # composite and is expanded into the others instead.
    simulated = declared - {"DEVICE_TYPE_EVERYTHING"}
    builders = _nested_dict_keys(coordinator, "_build_initial_state")
    assert builders, "no builders dict found"
    assert simulated <= builders[0], simulated - builders[0]

    updaters = _nested_dict_keys(coordinator, "_async_update_data")
    assert updaters, "no updaters dict found"
    assert simulated <= updaters[0], simulated - updaters[0]

    # Every self._foo referenced in those dicts must be a real method.
    methods = {
        n.name
        for n in ast.walk(coordinator)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for dispatch in ("_build_initial_state", "_async_update_data"):
        for referenced in _dispatch_targets(coordinator, dispatch):
            assert referenced in methods, f"{dispatch} points at missing {referenced}"

    # Every parent/child type needs a child list, and nothing else may have one:
    # a missing entry would KeyError while registering the devices.
    child_types = _set_literal_names(const, "CHILD_DEVICE_TYPES")
    assert child_types <= declared, child_types - declared
    assert _dict_keys(child_devices, "CHILDREN") == child_types

    # Child devices cannot be children of a child, so the composite leaves them out.
    composite = simulated - child_types

    print(
        f"wiring OK — {len(simulated)} device types, {len(platforms)} platforms, "
        f"{len(child_types)} with child devices, composite expands to {len(composite)}"
    )


def _stub_homeassistant() -> None:
    """Enough of Home Assistant to import coordinator.py, and no more."""

    def module(name: str, **attrs) -> types.ModuleType:
        mod = types.ModuleType(name)
        mod.__dict__.update(attrs)
        sys.modules[name] = mod
        return mod

    class Anything:
        """Stands in for a class the coordinator only annotates with."""

        def __class_getitem__(cls, item):
            return cls

        def __init__(self, *args, **kwargs) -> None:
            self.update_interval = kwargs.get("update_interval")
            self.data = None

        def async_set_updated_data(self, data) -> None:
            self.data = data

    class Platform(str):
        def __getattr__(self, name):  # pragma: no cover - attribute access only
            return name.lower()

    module("homeassistant")
    module("homeassistant.config_entries", ConfigEntry=Anything)
    module("homeassistant.core", HomeAssistant=Anything, callback=lambda f: f)
    module("homeassistant.const", Platform=Platform())
    module("homeassistant.exceptions", ConfigEntryError=Exception)
    module("homeassistant.util")
    # Only .hour is ever read, and the repo's own datetime.py shadows the
    # standard library module here.
    module("homeassistant.util.dt", now=lambda: types.SimpleNamespace(hour=12))
    module("homeassistant.helpers")
    module("homeassistant.helpers.update_coordinator", DataUpdateCoordinator=Anything)
    module("homeassistant.helpers.device_registry", DeviceInfo=Anything)


class _StubEntry:
    entry_id = "test_entry"
    title = "Test Strip"
    options: dict = {}
    data = {"device_type": "power_strip", "random_updates": False}


def demo_outlets() -> None:
    """Outlet power and energy must follow the switch, not the random walk."""
    _stub_homeassistant()
    # The integration's own datetime.py / time.py shadow the standard library
    # when this directory is on sys.path; import it as a package instead.
    sys.path = [p for p in sys.path if p not in ("", ".", str(HERE))]
    sys.path.insert(0, str(HERE.parent))
    sys.modules.setdefault(HERE.name, types.ModuleType(HERE.name))
    sys.modules[HERE.name].__path__ = [str(HERE)]
    coordinator_module = __import__(f"{HERE.name}.coordinator", fromlist=["x"])

    coordinator = coordinator_module.SimulatedDeviceCoordinator(None, _StubEntry())
    state = coordinator._build_initial_state()
    assert state["outlet_1_is_on"] is False
    assert state["total_power_w"] == 0.0

    # One hour with outlet 1 on: 40 W nominal -> 0.04 kWh, and the strip total
    # must follow. Random updates are off, so the draw is exactly nominal.
    state["outlet_1_is_on"] = True
    coordinator._settle_outlets(state, 3600.0)
    assert state["outlet_1_power_w"] == 40.0, state["outlet_1_power_w"]
    assert state["outlet_1_energy_kwh"] == 0.04, state["outlet_1_energy_kwh"]
    assert state["total_power_w"] == 40.0, state["total_power_w"]

    # Switching off stops the draw but keeps the meter.
    state["outlet_1_is_on"] = False
    coordinator._settle_outlets(state, 3600.0)
    assert state["outlet_1_power_w"] == 0.0
    assert state["outlet_1_energy_kwh"] == 0.04
    assert state["total_power_w"] == 0.0

    print("outlets OK — power follows the switch, energy accumulates")


if __name__ == "__main__":
    demo()
    demo_outlets()
