from collections import defaultdict

from makeproto import IService
from typing_extensions import (
    Any,
    AsyncGenerator,
    Callable,
    DefaultDict,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
)

from grpcAPI.exceptionhandler import ErrorCode, ExceptionRegistry
from grpcAPI.extract_types import extract_request_response_type
from grpcAPI.funclabel import set_label
from grpcAPI.interfaces import Validator
from grpcAPI.singleton import SingletonMeta
from grpcAPI.types import LabeledMethod


class APIService(IService):

    def __init__(
        self,
        name: str,
        options: Optional[List[str]] = None,
        comments: str = "",
        module: str = "service",
        package: str = "",
    ) -> None:
        self.name = name
        self.options = options or []
        self.comments = comments
        self.module = module
        self.package = package
        self.__methods: List[LabeledMethod] = []

    @property
    def methods(self) -> List[LabeledMethod]:
        return list(self.__methods)

    def __call__(
        self,
        func: Callable[..., Any],
        title: Optional[str] = None,
        description: str = "",
        tags: Optional[List[str]] = None,
        comment: Optional[str] = None,
        options: Optional[List[str]] = None,
    ) -> Callable[..., Any]:

        comment = comment or func.__doc__ or ""
        method_name = title or func.__name__
        tags = tags or []
        options = options or []

        set_label(func, self.package, self.module, self.name, method_name)
        requests, response_type = extract_request_response_type(func)
        labeled_method = LabeledMethod(
            name=method_name,
            method=func,
            package=self.package,
            module=self.module,
            service=self.name,
            comments=comment,
            description=description,
            request_types=requests,
            response_types=response_type,
            options=options,
            tags=tags,
        )

        self.__methods.append(labeled_method)
        return func


type DependencyRegistry = Dict[Callable[..., Any], Callable[..., Any]]

type Lifespan = Callable[[Any], AsyncGenerator[None, None]]

type CastDict = Dict[Tuple[Type[Any], Type[Any]], Callable[..., Any]]


class App(metaclass=SingletonMeta):

    def __init__(
        self,
        service_classes: List[IService],
        interceptors: List[Any],
        lifespan: Optional[Lifespan],
        _validator: Validator,
    ) -> None:
        self._service_classes = service_classes
        self._interceptors = interceptors
        self.lifespan = lifespan

        self._services: DefaultDict[str, List[IService]] = defaultdict(list)
        self.dependency_overrides: DependencyRegistry = {}
        self._exception_handlers: ExceptionRegistry = {}
        self._validator = _validator

    @property
    def services(self) -> Dict[str, List[IService]]:
        return dict(self._services)

    def add_service(self, service: APIService) -> None:
        for existing_service in self._services[service.package]:
            if existing_service.name == service.name:
                raise KeyError(
                    f"Service '{service.name}' already registered in package '{service.package}', module '{existing_service.module}'"
                )
        if self._validator:
            for method in service.methods:
                self._validator.inject_validation(method.method)
        self._services[service.package].append(service)

    def add_exception_handler(
        self,
        exc_type: Type[Exception],
        handler: Callable[[Exception], Tuple[ErrorCode, str]],
    ) -> None:
        self._exception_handlers[exc_type] = handler

    def exception_handler(self, exc_type: Type[Exception]) -> Callable[
        [Callable[[Exception], Tuple[ErrorCode, str]]],
        Callable[[Exception], Tuple[ErrorCode, str]],
    ]:
        def decorator(
            func: Callable[[Exception], Tuple[ErrorCode, str]],
        ) -> Callable[[Exception], Tuple[ErrorCode, str]]:
            self.add_exception_handler(exc_type, func)
            return func

        return decorator


# modificar a função acima...extrair castings e passar para app
# to be moved to grpcAPI-pydantic
# def get_models(func: Callable[..., Any], from_type: T, to_subclass: U) -> List[U]:
#     models: List[U] = []

#     return models


# def add_model(
#     func: Callable[..., Any],
#     from_type: T,
#     to_subclass: U,
#     cast: Callable[[T], U],
# ) -> Dict[Tuple[T, U], Callable[[T], U]]:

#     casts: Dict[Tuple[T, U], Callable[[T], U]] = {}
#     models = get_models(func, from_type, to_subclass)
#     for model in models:
#         key = (from_type, model)
#         casts[key] = cast
#     return casts
