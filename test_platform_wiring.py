"""Static wiring checks — run with `python3 test_platform_wiring.py`.

These parse the source instead of importing it, so they run without Home
Assistant installed. They catch the mistakes this integration is actually
prone to: a platform listed in PLATFORMS with no module behind it, or a device
type that no coordinator builder knows how to create state for.
"""

from __future__ import annotations

import ast
import pathlib

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


def demo() -> None:
    const = _tree("const.py")
    coordinator = _tree("coordinator.py")
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

    print(
        f"wiring OK — {len(simulated)} device types, {len(platforms)} platforms, "
        f"composite expands to {len(simulated)}"
    )


if __name__ == "__main__":
    demo()
