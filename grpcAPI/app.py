from collections import defaultdict
from logging import Logger
from typing import (
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

from makeproto import ILabeledMethod, IService

from grpcAPI.exceptionhandler import ErrorCode, ExceptionRegistry
from grpcAPI.funclabel import set_label

type MakeLabeledMethod = Callable[
    [
        Callable[..., Any],
        str,
        str,
        str,
        str,
        str,
        str,
        List[str],
        List[str],
    ],
    ILabeledMethod,
]


class BaseService(IService):

    def __init__(
        self,
        label_method: MakeLabeledMethod,
        name: str,
        options: Optional[List[str]] = None,
        comments: str = "",
        module: str = "service",
        package: str = "",
        process_service: Optional[Callable[["BaseService"], None]] = None,
    ) -> None:
        self.name = name
        self.__label_method = label_method
        self.options = options or []
        self.comments = comments
        self.module = module
        self.package = package
        self.__methods: List[ILabeledMethod] = []
        self.__process_service = process_service

    @property
    def methods(self) -> List[ILabeledMethod]:
        return list(self.__methods)

    def process_service(self) -> None:
        if self.__process_service is not None:
            self.__process_service(self)

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

        labeled_method = self.__label_method(
            func,
            self.package,
            self.module,
            self.name,
            method_name,
            comment,
            description,
            options,
            tags,
        )
        self.__methods.append(labeled_method)
        return func


type DependencyRegistry = Dict[Callable[..., Any], Callable[..., Any]]

type Lifespan = Callable[[Any], AsyncGenerator[None, None]]

type CastDict = Dict[Tuple[Type[Any], Type[Any]], Callable[..., Any]]


class App:

    def __init__(
        self,
        caster: CastDict,
        add_casting: Optional[Callable[[Callable[..., Any]], CastDict]] = None,
        lifespan: Optional[Lifespan] = None,
        logger: Optional[Logger] = None,
        error_log: Optional[Callable[[str, Exception], None]] = None,
    ) -> None:
        self.lifespan = lifespan
        self._logger = logger
        self._error_log = error_log
        self._add_casting = add_casting
        self._caster = caster

        self._services: DefaultDict[str, List[IService]] = defaultdict(list)
        self.dependency_overrides: DependencyRegistry = {}
        self._exception_handlers: ExceptionRegistry = {}

    @property
    def casting_dict(self) -> Dict[Tuple[type[Any], Type[Any]], Callable[..., Any]]:
        return self._caster

    @property
    def services(self) -> Dict[str, List[IService]]:
        return dict(self._services)

    def _add_casting_models(self, methods: List[ILabeledMethod]) -> None:
        funcs = [func.method for func in methods]
        if self._add_casting is not None:
            for func in funcs:
                models = self._add_casting(func)
                self._caster.update(models)

    def add_service(self, service: BaseService) -> None:
        for existing_service in self._services[service.package]:
            if existing_service.name == service.name:
                raise KeyError(
                    f"Service '{service.name}' already registered in package '{service.package}', module '{existing_service.module}'"
                )
        service.process_service()
        self._add_casting_models(service.methods)
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
