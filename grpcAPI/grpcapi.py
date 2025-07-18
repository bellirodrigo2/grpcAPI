from makeproto import IService
from typing_extensions import List, Optional, Type

from grpcAPI.app import App, Lifespan, Middleware

# try:
# from pydantic import BaseModel # na verdade aqui importa de outro file
# validator = STD_VALIDATOR()
# validator = PYDANTIC_VALIDATOR()
# except ImportError:
from grpcAPI.inject_validation import StdValidator
from grpcAPI.process_service.format_service import FormatServiceFactory

validator = StdValidator()


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
