from typing import Any, List, Optional

from makeproto import IService

from grpcAPI.app import App, Lifespan
from grpcAPI.inject_validation import StdValidator


def GrpcAPI(
    service_classes: Optional[List[IService]] = None,
    interceptors: Optional[List[Any]] = None,
    lifespan: Optional[Lifespan] = None,
) -> App:
    service_classes = service_classes or []
    interceptors = interceptors or []
    return App(
        service_classes=service_classes,
        interceptors=interceptors,
        lifespan=lifespan,
        _validator=StdValidator(),
    )
