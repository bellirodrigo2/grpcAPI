from typemapping import get_func_args
from typing_extensions import Any, Callable, Sequence, Tuple

from grpcAPI.app import App
from grpcAPI.makeproto import IService
from grpcAPI.types import Depends


def get_func_list() -> Sequence[IService]:
    app = App()
    return app.service_list


def is_service_dependent(service: IService, dep_func: Callable[..., Any]) -> bool:
    for method in service.methods:
        for arg in get_func_args(method.method):
            instance = arg.getinstance(Depends)
            if instance is not None and instance.default == dep_func:
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
        # passar args de dep_func para self.run
        # iniciar healtcheck e adicionar ao self

    def run(self, **kwargs: Any) -> Any:

        try:
            resp = self.dep_func(**kwargs)
            if not self.is_active:
                # alterar todos os healtcheck para serving
                pass
            return resp
        except self.exceptions:
            if self.is_active:
                # alterar todos os healtcheck para not serving
                pass
