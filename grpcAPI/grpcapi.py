from makeproto import IService
from typing_extensions import List, Optional, Type

from grpcAPI.app import App, Lifespan
from grpcAPI.config import STD_VALIDATOR
from grpcAPI.interfaces import Middleware
from grpcAPI.process_service.format_service import FormatServiceFactory


def GrpcAPI(
    service_classes: Optional[List[IService]] = None,
    middlewares: Optional[List[Type[Middleware]]] = None,
    lifespan: Optional[Lifespan] = None,
) -> App:
    service_classes = service_classes or []
    middlewares = middlewares or []
    return App(
        service_classes=service_classes,
        middleware=middlewares,
        lifespan=lifespan,
        _validator=STD_VALIDATOR(),
        _process_service_factories=[FormatServiceFactory()],
    )
