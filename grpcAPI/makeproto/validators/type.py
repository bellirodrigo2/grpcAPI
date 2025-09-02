import inspect
from collections.abc import AsyncIterator

from typing_extensions import Any, Callable, List

from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.interface import IMetaType
from grpcAPI.makeproto.report import CompileErrorCode, CompileReport
from grpcAPI.makeproto.template import MethodTemplate, ServiceTemplate


def is_async_func(func: Callable[..., Any]) -> bool:
    return inspect.isasyncgenfunction(func)


class TypeValidator(CompilerPass):

    def visit_service(self, block: ServiceTemplate) -> None:
        for field in block.methods:
            field.accept(self)

    def _check_requests(
        self, name: str, report: CompileReport, requests: List[IMetaType]
    ) -> None:
        msg = None
        # checar se há algum non injectable...
        invalid_req = CompileErrorCode.METHOD_INVALID_REQUEST_TYPE
        if len(requests) == 0:
            msg = "Method must define a request message."
        elif len(requests) > 1:
            sets = {x.basetype for x in requests}
            if len(sets) == 1:
                msg = "Stream and Single request mixed in the args"
            else:
                msg = f"Only one request message allowed per method. Found {[req.argtype.__name__ for req in requests]}"
        if msg is not None:
            report.report_error(code=invalid_req, location=name, override_msg=msg)

    def _check_response(self, method: MethodTemplate) -> None:
        report: CompileReport = self.ctx.get_report(method.service)
        if method.response_type is None:
            override_msg = "Response type is 'None'"
            report.report_error(
                CompileErrorCode.METHOD_INVALID_RESPONSE_TYPE,
                location=method.name,
                override_msg=override_msg,
            )
        else:
            is_func_async = is_async_func(method.method_func)
            is_return_async = method.response_type.origin is AsyncIterator
            consistency = is_return_async == is_func_async
            if not consistency:
                report.report_error(
                    code=CompileErrorCode.METHOD_NOT_CONSISTENT_TO_RETURN,
                    location=method.name,
                )

    def visit_method(self, method: MethodTemplate) -> None:
        report: CompileReport = self.ctx.get_report(method.service)
        self._check_requests(method.name, report, method.request_types)
        self._check_response(method)
