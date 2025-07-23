from collections.abc import AsyncIterator

from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.interface import IMetaType
from grpcAPI.makeproto.report import CompileErrorCode, CompileReport
from grpcAPI.makeproto.template import MethodTemplate, ServiceTemplate


def get_type_str(bt: IMetaType, package: str) -> str:
    cls_name = bt.basetype.__name__
    cls_package = bt.package
    if not cls_package or cls_package == package:
        return cls_name
    return f"{cls_package}.{cls_name}"


class TypeSetter(CompilerPass):

    def visit_service(self, block: ServiceTemplate) -> None:
        for field in block.methods:
            field.accept(self)

    def visit_method(self, method: MethodTemplate) -> None:
        try:
            request_arg = method.request_types[0]
            request_stream = request_arg.origin is AsyncIterator
            request_str = get_type_str(request_arg, method.service.package)
            method.request_str = request_str
            method.request_stream = request_stream

            response_arg = method.response_type
            response_stream = response_arg.origin is AsyncIterator
            response_str = get_type_str(response_arg, method.service.package)
            method.response_str = response_str
            method.response_stream = response_stream

        except (AttributeError, IndexError) as e:
            report: CompileReport = self.ctx.get_report(method.service)
            report.report_error(
                CompileErrorCode.SETTER_PASS_ERROR,
                method.name,
                f"TypeSetter.visit_method: {str(e)}",
            )
