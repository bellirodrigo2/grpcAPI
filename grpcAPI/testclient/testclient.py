import inspect
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from grpcAPI.app import App
from grpcAPI.make_method import make_method_async
from grpcAPI.process_service import ProcessService
from grpcAPI.proto_build import make_protos
from grpcAPI.testclient.contextmock import ContextMock
from grpcAPI.types import AsyncContext

default_test_settings = {
    "lint": True,
    "compile_proto": {"clean_services": True, "overwrite": False},
}


class TestClient:
    __test__ = False

    def __init__(
        self,
        app: App,
        settings: Dict[str, Any],
        process_service_factory: Optional[
            List[Callable[[Mapping[str, Any]], ProcessService]]
        ] = None,
    ) -> None:

        settings = {**settings, **default_test_settings}

        process_service_factory = process_service_factory or []
        process_service_factory.extend(app._process_service_factories)
        process_services = [
            factory(settings) for factory in set(process_service_factory)
        ]
        for service in app.service_list:
            for proc in process_services:
                proc(service)
        if settings["lint"]:
            make_protos(app.services, app._casting_list)

        self._services: Dict[Tuple[str, str, str], Callable[..., Any]] = {}
        for service in app.service_list:
            for method in service.methods:
                rpc_method = make_method_async(
                    labeledmethod=method,
                    overrides=app.dependency_overrides,
                    exception_registry=app._exception_handlers,
                )
                tuple_id = (service.package, service.name, method.name)
                self._services[tuple_id] = rpc_method
                method.method.__label__ = tuple_id

    async def run_by_label(
        self,
        package: str,
        service_name: str,
        method_name: str,
        request: Any,
        context: Optional[AsyncContext] = None,
    ) -> Any:

        context = context or ContextMock()
        method = self._services.get((package, service_name, method_name), None)
        if method is None:
            raise KeyError(f'No Method Found: "{package}/{service_name}/{method_name}"')

        response = method(request, context)
        if inspect.isawaitable(response):
            response = await response

        return response

    async def run(
        self,
        func: Callable[..., Any],
        request: Any,
        context: Optional[AsyncContext] = None,
    ) -> Any:

        label = func.__label__
        if label is None:
            raise Exception(
                f'Function "{func.__name__}" is not linked to a grpcAPI module'
            )
        package, _, service_name, method_name = label

        return await self.run_by_label(
            package, service_name, method_name, request, context
        )
