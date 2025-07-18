from typing_extensions import Callable

from grpcAPI.interfaces import ServerPlugin
from grpcAPI.server_plugins.loader import load_plugins

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
