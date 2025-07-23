from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.report import CompileErrorCode, CompileReport
from grpcAPI.makeproto.template import ProtoTemplate, ServiceTemplate


class ServiceSetter(CompilerPass):

    def visit_service(self, block: ServiceTemplate) -> None:
        module_template: ProtoTemplate = self.ctx.get_state(block.module)
        services = module_template.services
        if block in services:
            report: CompileReport = self.ctx.get_report(block)
            report.report_error(
                CompileErrorCode.SETTER_PASS_ERROR,
                block.name,
                f"Service '{block.name}' already exists on ProtoTemplate<{block.package},{block.module}>",
            )
        services.append(block)
