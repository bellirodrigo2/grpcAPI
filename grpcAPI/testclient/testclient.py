import inspect
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from grpcAPI.app import App
from grpcAPI.interfaces import ProcessService
from grpcAPI.make_method import make_method_async
from grpcAPI.testclient.contextmock import ContextMock
from grpcAPI.types import AsyncContext


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

        process_service_factory = process_service_factory or []
        process_service_factory.extend(app._process_service_factories)
        process_services = [
            factory(settings) for factory in set(process_service_factory)
        ]

        self._services: Dict[Tuple[str, str, str], Callable[..., Any]] = {}
        services = [item for sublist in app.services.values() for item in sublist]
        for service in services:
            for proc in process_services:
                proc(service)
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
