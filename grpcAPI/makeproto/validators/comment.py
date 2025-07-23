from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.report import CompileErrorCode
from grpcAPI.makeproto.template import MethodTemplate, ServiceTemplate


class CommentsValidator(CompilerPass):

    def visit_service(self, block: ServiceTemplate) -> None:
        report = self.ctx.get_report(block)
        if not isinstance(block.comments, str):
            report.report_error(
                code=CompileErrorCode.INVALID_COMMENT,
                location=block.name,
            )
        for field in block.methods:
            field.accept(self)

    def visit_method(self, method: MethodTemplate) -> None:
        report = self.ctx.get_report(method.service)

        if not isinstance(method.comments, str):
            report.report_error(
                code=CompileErrorCode.INVALID_COMMENT,
                location=method.name,
            )
