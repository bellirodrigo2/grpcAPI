from typing_extensions import Any, Dict, Type


class SingletonMeta(type):
    _instances: Dict[Any, Any] = {}

    def __call__(cls: Type[Any], *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
