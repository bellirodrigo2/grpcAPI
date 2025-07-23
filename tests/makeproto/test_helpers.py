from typing import Any, Callable, List, Optional, Type

from grpcAPI.makeproto.template import MethodTemplate, ServiceTemplate
from tests.conftest import make_metatype_from_type


def make_service(
    name: str,
    package: str = "",
    module: str = "",
    comments: str = "",
    options: Optional[List[str]] = None,
    methods: Optional[List[MethodTemplate]] = None,
) -> ServiceTemplate:
    service_template = ServiceTemplate(
        name=name,
        package=package,
        module=module,
        comments=comments,
        options=options or [],
        methods=methods or [],
    )
    return service_template


def make_method(
    name: str,
    method: Optional[Callable[..., Any]] = None,
    service: Optional[ServiceTemplate] = None,
    requests: Optional[List[Type[Any]]] = None,
    response: Optional[Type[Any]] = None,
    comments: str = "",
    options: Optional[List[str]] = None,
    request_stream: bool = False,
    response_stream: bool = False,
) -> MethodTemplate:

    service = service or make_service("mock_service")

    if requests is None:
        requests_ = []
    else:
        requests_ = [make_metatype_from_type(req) for req in requests]

    if response is None:
        response_ = None
    else:
        response_ = make_metatype_from_type(response)

    method_template = MethodTemplate(
        method_func=method,
        name=name,
        options=options or [],
        comments=comments,
        request_types=requests_,
        response_type=response_,
        service=service,
        request_stream=request_stream,
        response_stream=response_stream,
    )
    service.methods.append(method_template)
    return method_template
