import itertools
from collections import defaultdict
from typing import Iterable

from grpc import aio
from typing_extensions import (
    Any,
    AsyncGenerator,
    Callable,
    DefaultDict,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    Union,
)

from grpcAPI import ExceptionRegistry
from grpcAPI.data_types import AsyncContext
from grpcAPI.label_method import make_labeled_method
from grpcAPI.makeproto import ILabeledMethod, IService
from grpcAPI.singleton import SingletonMeta

Middleware = aio.ServerInterceptor


class APIService(IService):

    def __init__(
        self,
        name: str,
        options: Optional[List[str]] = None,
        comments: str = "",
        module: str = "service",
        package: str = "",
        title: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
        module_level_options: Optional[Iterable[str]] = None,
        module_level_comments: Optional[Iterable[str]] = None,
    ) -> None:
        self.title = title or name
        self.description = description
        self.tags = tags or []
        self.name = name
        self.options = options or []
        self.comments = comments
        self.module = module
        self.package = package
        self.module_level_options = module_level_options or []
        self.module_level_comments = module_level_comments or []
        self.__methods: List[ILabeledMethod] = []

    @property
    def methods(self) -> List[ILabeledMethod]:
        return list(self.__methods)

    @property
    def qual_name(self) -> str:
        service_name = self.name
        if self.package:
            service_name = f"{self.package}.{self.name}"
        return service_name

    def _register_method(
        self,
        func: Callable[..., Any],
        title: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
        comment: Optional[str] = None,
        options: Optional[List[str]] = None,
    ) -> Callable[..., Any]:
        comment = comment or func.__doc__ or ""
        title = title or func.__name__

        labeled_method = make_labeled_method(
            title,
            func,
            self.package,
            self.module,
            self.name,
            comment,
            description,
            options,
            tags,
        )

        self.__methods.append(labeled_method)
        return func

    def __call__(
        self,
        func: Optional[Callable[..., Any]] = None,
        *,
        title: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
        comment: Optional[str] = None,
        options: Optional[List[str]] = None,
    ) -> Union[Callable[..., Any], Callable[[Callable[..., Any]], Callable[..., Any]]]:
        if func is not None and callable(func):
            # Called as @serviceapi
            return self._register_method(func)
        else:
            # Called as @serviceapi(...)
            def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
                return self._register_method(
                    f,
                    title=title,
                    description=description,
                    tags=tags,
                    comment=comment,
                    options=options,
                )

            return decorator


DependencyRegistry = Dict[Callable[..., Any], Callable[..., Any]]

Lifespan = Callable[[Any], AsyncGenerator[None, None]]


class App(metaclass=SingletonMeta):

    def __init__(
        self,
        lifespan: Optional[Lifespan] = None,
    ) -> None:
        self._service_classes = []
        self._middleware = []
        self.lifespan = lifespan

        self._services: DefaultDict[str, List[IService]] = defaultdict(list)
        self.dependency_overrides: DependencyRegistry = {}
        self._exception_handlers: ExceptionRegistry = {}

    @property
    def services(self) -> Mapping[str, List[IService]]:
        return dict(self._services)

    @property
    def service_list(self) -> Sequence[IService]:
        return list(itertools.chain.from_iterable(self._services.values()))

    def add_service(self, service: APIService) -> None:
        for existing_service in self._services[service.package]:
            if existing_service.name == service.name:
                raise KeyError(
                    f"Service '{service.name}' already registered in package '{service.package}', module '{existing_service.module}'"
                )
        self._services[service.package].append(service)

    def add_middleware(self, middleware: Type[Middleware]) -> None:
        self._middleware.append(middleware)

    def middleware(self) -> Callable[[Type[Middleware]], Type[Middleware]]:
        def decorator(cls: Type[Middleware]) -> Type[Middleware]:
            self.add_middleware(cls)
            return cls

        return decorator

    def add_exception_handler(
        self,
        exc_type: Type[Exception],
        handler: Callable[[Exception, AsyncContext], None],
    ) -> None:
        self._exception_handlers[exc_type] = handler

    def exception_handler(self, exc_type: Type[Exception]) -> Callable[
        [Callable[[Exception, AsyncContext], None]],
        Callable[[Exception, AsyncContext], None],
    ]:
        def decorator(
            func: Callable[[Exception, AsyncContext], None],
        ) -> Callable[[Exception, AsyncContext], None]:
            self.add_exception_handler(exc_type, func)
            return func

        return decorator
