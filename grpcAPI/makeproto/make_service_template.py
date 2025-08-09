from typing_extensions import List

from grpcAPI.makeproto.interface import IService
from grpcAPI.makeproto.template import MethodTemplate, ServiceTemplate


def make_service_template(
    service: IService,
) -> ServiceTemplate:

    service_template = ServiceTemplate(
        name=service.name,
        package=service.package,
        module=service.module,
        comments=service.comments,
        options=service.options,
        methods=[],
    )
    methods: List[MethodTemplate] = []

    for labeledmethod in service.methods:
        if not labeledmethod.active:
            continue
        method = labeledmethod.method

        method_template = MethodTemplate(
            method_func=method,
            name=labeledmethod.name,
            options=labeledmethod.options,
            comments=labeledmethod.comments,
            request_types=labeledmethod.request_types,
            response_type=labeledmethod.response_types,
            service=service_template,
            request_stream=False,
            response_stream=False,
        )
        methods.append(method_template)
    service_template.methods = methods
    return service_template
