from typing_extensions import List, Optional, Type

from grpcAPI.app import App, Lifespan, Middleware
from grpcAPI.makeproto import IService
from grpcAPI.process_service.format_service import FormatServiceFactory

try:
    from grpcAPI.validators.inject_pydantic_validation import (
        PydanticValidator as Validator,
    )
except ImportError:  # pragma: no cover
    from grpcAPI.validators.inject_validation import StdValidator as Validator

validator = Validator()


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
        _casting_list=validator.casting_list,
        _process_service_factories=[FormatServiceFactory(), lambda _: validator],
    )
