from collections import defaultdict
from dataclasses import dataclass
from logging import Logger

from makeproto import ILabeledMethod, IMetaType, IService
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
from grpcAPI.funclabel import set_label
from grpcAPI.interface import ExtractMetaType
from grpcAPI.singleton import SingletonMeta


@dataclass
class LabeledMethod(ILabeledMethod):
    name: str
    method: Callable[..., Any]
    package: str
    module: str
    service: str
    comments: str
    description: str
    options: List[str]
    tags: List[str]

    request_types: List[IMetaType]
    response_types: Optional[IMetaType]


class BaseService(IService):

    def __init__(
        self,
        extract_metatypes: ExtractMetaType,
        name: str,
        options: Optional[List[str]] = None,
        comments: str = "",
        module: str = "service",
        package: str = "",
        # process_service: Optional[Callable[["BaseService"], None]] = None,
    ) -> None:
        self.name = name
        self.__extract_metatypes = extract_metatypes
        self.options = options or []
        self.comments = comments
        self.module = module
        self.package = package
        self.__methods: List[ILabeledMethod] = []
        # self.__process_service = process_service

    @property
    def methods(self) -> List[ILabeledMethod]:
        return list(self.__methods)

    # def process_service(self) -> None:
    # if self.__process_service is not None:
    # self.__process_service(self)

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
        requests, response_type = self.__extract_metatypes(func)
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
        caster: Optional[CastDict] = None,
        process_service: Optional[Callable[["App", BaseService], None]] = None,
        lifespan: Optional[Lifespan] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self.lifespan = lifespan
        self._logger = logger
        self.__process_service = process_service
        self._caster = caster or {}

        self._services: DefaultDict[str, List[IService]] = defaultdict(list)
        self.dependency_overrides: DependencyRegistry = {}
        self._exception_handlers: ExceptionRegistry = {}

    @property
    def casting_dict(self) -> Dict[Tuple[type[Any], Type[Any]], Callable[..., Any]]:
        return self._caster

    @property
    def services(self) -> Dict[str, List[IService]]:
        return dict(self._services)

    def add_service(self, service: BaseService) -> None:
        for existing_service in self._services[service.package]:
            if existing_service.name == service.name:
                raise KeyError(
                    f"Service '{service.name}' already registered in package '{service.package}', module '{existing_service.module}'"
                )
        if self.__process_service is not None:
            self.__process_service(self, service)
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


def base_process_service(
    app: App,
    service: BaseService,
    format_name: Callable[[str], str],
    format_comment: Callable[[BaseService], str],
    transform_func: Callable[[Callable[..., Any]], Callable[..., Any]],
) -> None:

    service.name = format_name(service.name)
    service.comments = format_comment(service)
    for method in service.methods:
        transform_func(method.method)


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
