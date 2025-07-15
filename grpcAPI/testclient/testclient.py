import inspect

from typing_extensions import Any, Callable, Dict, Optional, Tuple

from grpcAPI.app import App
from grpcAPI.context import AsyncContext
from grpcAPI.funclabel import get_label
from grpcAPI.module_loader import ModuleLoader
from grpcAPI.service_provider import provide_services
from grpcAPI.testclient import ContextMock


class TestClient:
    __test__ = False

    def __init__(self, app: App, settings: Dict[str, Any]) -> None:

        module_loader = ModuleLoader(app, settings)
        services = [item for sublist in app.services.values() for item in sublist]

        self.services: Dict[Tuple[str, str], Any] = {}
        for service_cls in provide_services(
            services=services,
            modules=module_loader.modules_dict,
            overrides=app.dependency_overrides,
            exception_registry=app._exception_handlers,
        ):
            instance = service_cls()
            self.services[instance._get_label()] = instance

    async def run_by_label(
        self,
        package: str,
        service_name: str,
        method_name: str,
        request: Any,
        context: Optional[AsyncContext] = None,
    ) -> Any:

        context = context or ContextMock()
        service = self.services.get((package, service_name), None)
        if service is None:
            raise KeyError(f'No service found: "{package}/{service_name}"')

        method = getattr(service, method_name)

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

        label = get_label(func)
        if label is None:
            raise Exception(
                f'Function "{func.__name__}" is not linked to a grpcAPI module'
            )
        package, _, service_name, method_name = label

        return await self.run_by_label(
            package, service_name, method_name, request, context
        )
