import threading

from typing_extensions import Any, Dict, Type


class SingletonMeta(type):
    _instances: Dict[Type[Any], Any] = {}
    _lock = threading.Lock()

    def __call__(cls: Type[Any], *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)

        return cls._instances[cls]
