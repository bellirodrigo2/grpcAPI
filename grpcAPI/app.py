import itertools
from collections import defaultdict
from typing import Never

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
from grpcAPI.process_service import ProcessService
from grpcAPI.singleton import SingletonMeta

Middleware = aio.ServerInterceptor


class MetaData:

    def __init__(
        self,
        name: str,
        options: Optional[List[str]] = None,
        comments: Optional[List[str]] = None,
    ):
        self.name = name
        self.options: List[str] = options or []
        self.comments: List[str] = comments or []


class APIModule(MetaData):

    def __init__(
        self,
        name: str,
        package: str = "",
        options: Optional[List[str]] = None,
        comments: Optional[List[str]] = None,
    ):
        self.package = package
        self.services: List[APIService] = []
        super().__init__(name, options, comments)

    def make_service(
        self,
        service_name: str,
        options: Optional[List[str]] = None,
        comments: str = "",
        title: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> "APIService":
        service = APIService(
            name=service_name,
            module=self.name,
            package=self.package,
            title=title,
            description=description,
            tags=tags,
            options=options,
            comments=comments,
            module_level_options=self.options,
            module_level_comments=self.comments,
        )
        self.services.append(service)
        return service


class APIPackage(MetaData):

    def __init__(
        self,
        name: str,
        options: Optional[List[str]] = None,
        comments: Optional[List[str]] = None,
    ):
        self.modules: List[APIModule] = []
        super().__init__(name, options, comments)

    def make_module(
        self,
        module_name: str,
        options: Optional[List[str]] = None,
        comments: Optional[List[str]] = None,
    ) -> APIModule:
        options = options or []
        comments = comments or []
        module = APIModule(
            name=module_name,
            package=self.name,
            comments=list(set(comments + self.comments)),
            options=list(set(options + self.options)),
        )
        self.modules.append(module)
        return module


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
        module_level_options: Optional[List[str]] = None,
        module_level_comments: Optional[List[str]] = None,
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
        self.active = True

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
        request_type_input: Optional[Type[Any]] = None,
        response_type_input: Optional[Type[Any]] = None,
    ) -> Callable[..., Any]:
        comment = comment or func.__doc__ or ""
        title = title or func.__name__

        labeled_method = make_labeled_method(
            title,
            func=func,
            package=self.package,
            module=self.module,
            service=self.name,
            comment=comment,
            description=description,
            tags=options,
            options=tags,
            request_type_input=request_type_input,
            response_type_input=response_type_input,
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
        request_type_input: Optional[Type[Any]] = None,
        response_type_input: Optional[Type[Any]] = None,
    ) -> Union[Callable[..., Any], Callable[[Callable[..., Any]], Callable[..., Any]]]:
        if func is not None and callable(func):
            # Called as @serviceapi
            return self._register_method(func)
        else:
            # Called as @serviceapi(...)
            def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
                return self._register_method(
                    func=f,
                    title=title,
                    description=description,
                    tags=tags,
                    comment=comment,
                    options=options,
                    request_type_input=request_type_input,
                    response_type_input=response_type_input,
                )

            return decorator


DependencyRegistry = Dict[Callable[..., Any], Callable[..., Any]]

Lifespan = Callable[["App"], AsyncGenerator[Never, bool]]


class App:

    def __init__(
        self,
        lifespan: Optional[List[Lifespan]] = None,
        server: Optional[Any] = None,
    ) -> None:
        self._service_classes = []
        self._middleware = []
        self.lifespan = lifespan or []
        self.server = server

        self._services: DefaultDict[str, List[IService]] = defaultdict(list)
        self.dependency_overrides: DependencyRegistry = {}
        self._exception_handlers: ExceptionRegistry = {}
        self._process_service: List[ProcessService] = []

    @property
    def services(self) -> Mapping[str, List[IService]]:
        return dict(self._services)

    @property
    def service_list(self) -> Sequence[IService]:
        return list(itertools.chain.from_iterable(self._services.values()))

    def add_service(self, service: Union[APIService, APIModule, APIPackage]) -> None:
        if isinstance(service, APIService):
            self._add_service(service)
        elif isinstance(service, APIModule):
            self._add_module(service)
        elif isinstance(service, APIPackage):
            self._add_package(service)
        else:
            raise TypeError(
                f"Expected APIService, APIModule, or APIPackage, got {type(service).__name__}"
            )

    def _add_service(self, service: APIService) -> None:
        for existing_service in self._services[service.package]:
            if existing_service.name == service.name:
                raise KeyError(
                    f"Service '{service.name}' already registered in package '{service.package}', module '{existing_service.module}'"
                )
        self._services[service.package].append(service)

    def _add_module(self, module: "APIModule") -> None:
        for service in module.services:
            self._add_service(service)

    def _add_package(self, package: "APIPackage") -> None:
        for module in package.modules:
            self._add_module(module)

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


class GrpcAPI(App, metaclass=SingletonMeta):
    pass
