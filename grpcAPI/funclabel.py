from typing import Any, Callable, Optional, Tuple


def set_label(
    func: Callable[..., Any], package: str, module: str, service: str, methodname: str
) -> None:
    func.__service_label__ = (package, module, service, methodname)


def has_label(func: Callable[..., Any]) -> bool:
    return hasattr(func, "__service_label__")


def get_label(func: Callable[..., Any]) -> Optional[Tuple[str, str, str, str]]:
    if not has_label(func):
        return None
    return func.__service_label__
