"""A simple plugin loader."""

import importlib.util

from grpcAPI.config import plugin_path


class ModuleInterface:
    """Represents a plugin interface. A plugin has a single register function."""

    @staticmethod
    def register() -> None:
        """Register the necessary items in the game character factory."""


def load_plugins(plugins: list[str]) -> None:
    """Loads the plugins defined in the plugins list."""
    base_path = plugin_path
    for plugin_file in plugins:
        path = base_path / f"{plugin_file}.py"
        spec = importlib.util.spec_from_file_location(plugin_file, path)
        if spec is None:
            raise FileNotFoundError(
                f"Can´t load plugin: {plugin_file} at {plugin_path}"
            )
        plugin = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin)
        plugin.register()
