from typemapping import get_func_args
from typing_extensions import Any, Callable, Sequence, Tuple

from grpcAPI.app import App
from grpcAPI.datatypes import Depends
from grpcAPI.makeproto import IService


def get_func_list() -> Sequence[IService]:
    app = App()
    return app.service_list


def is_service_dependent(service: IService, dep_func: Callable[..., Any]) -> bool:
    for method in service.methods:
        for arg in get_func_args(method.method):
            instance = arg.getinstance(Depends)
            if instance is not None:
                if instance.default == dep_func:
                    return True
                # protect against circular dependencies
                if is_service_dependent(service, instance.default):
                    return True
    return False


def map_dependents(dep_func: Callable[..., Any]) -> Sequence[str]:
    return [
        service.qual_name
        for service in get_func_list()
        if is_service_dependent(service, dep_func)
    ]


class StatefulService:

    def __init__(
        self,
        dep_func: Callable[..., Any],
        exceptions: Tuple[BaseException],
        is_active: bool,
    ) -> None:
        self.dep_func = dep_func
        self.dependents = map_dependents(dep_func)
        self.is_active = is_active
        self.exceptions = exceptions
        # pass dep_func args to self.run
        # start healthcheck and add to self

    def run(self, **kwargs: Any) -> Any:

        try:
            resp = self.dep_func(**kwargs)
            if not self.is_active:
                # change all healthcheck to serving
                pass
            return resp
        except self.exceptions:
            if self.is_active:
                # change all healthcheck to not serving
                pass
