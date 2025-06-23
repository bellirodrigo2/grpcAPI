import importlib.util


def load_app(app_path: str) -> None:
    spec = importlib.util.spec_from_file_location("app_module", app_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load app module from {app_path}")

    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
