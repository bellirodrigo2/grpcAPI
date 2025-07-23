from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.interface import IMetaType
from grpcAPI.makeproto.report import CompileErrorCode, CompileReport
from grpcAPI.makeproto.template import MethodTemplate, ServiceTemplate


class ImportsValidator(CompilerPass):

    def visit_service(self, block: ServiceTemplate) -> None:
        for field in block.methods:
            field.accept(self)

    def _check_proto_path(
        self, btype: IMetaType, method_name: str, arg: str, report: CompileReport
    ) -> None:
        if not btype.proto_path:
            report.report_error(
                code=CompileErrorCode.INVALID_CLASS_PROTO_PATH,
                location=method_name,
                override_msg=f"{arg} class '{btype.basetype.__name__}' has no proto_path associated",
            )

    def visit_method(self, method: MethodTemplate) -> None:
        report = self.ctx.get_report(method.service)
        if not method.request_types:
            # should raise a compiler error on the types validator
            return
        request_type = method.request_types[0]
        self._check_proto_path(request_type, method.name, "Request", report)

        response_type = method.response_type
        if response_type is None:
            # should raise a compiler error on the types validator
            return
        self._check_proto_path(response_type, method.name, "Response", report)
