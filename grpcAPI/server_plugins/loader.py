import importlib.util
from pathlib import Path

from typing_extensions import Callable

from grpcAPI.server_plugins import ServerPlugin

_get_plugin: dict[str, Callable[..., ServerPlugin]] = {}


def register(plugin_name: str, create_plugin: Callable[..., ServerPlugin]) -> None:
    """Register a new plugin type."""
    _get_plugin[plugin_name] = create_plugin


def unregister(plugin_name: str) -> None:
    """Unregister a plugin type."""
    _get_plugin.pop(plugin_name, None)


def get_plugin(plugin_name: str) -> ServerPlugin:

    try:
        if plugin_name not in _get_plugin:
            load_plugins([plugin_name])
        creator_func = _get_plugin[plugin_name]
    except FileNotFoundError as e:
        raise ValueError(str(e))

    plugin = creator_func()
    return plugin


class ModuleInterface:
    """Represents a plugin interface. A plugin has a single register function."""

    @staticmethod
    def register() -> None:
        """Register the necessary plugin."""


def load_plugins(plugins: list[str]) -> None:
    """Loads the plugins defined in the plugins list."""
    base_path = (Path(__file__).parent / "plugins").resolve()
    for plugin_file in plugins:
        path = base_path / f"{plugin_file}.py"
        spec = importlib.util.spec_from_file_location(plugin_file, path)
        if spec is None:
            raise FileNotFoundError(f"Can´t load plugin: {plugin_file} at {base_path}")
        plugin = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin)
        plugin.register()
