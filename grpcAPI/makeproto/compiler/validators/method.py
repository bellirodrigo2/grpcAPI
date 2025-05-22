from typing import Any, Optional

from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.compiler.report import CompileReport
from grpcAPI.makeproto.protoblock import Method
from grpcAPI.makeproto.protoobj.message import BaseMessage


class MethodValidator(CompilerPass):
    def visit_method(self, method: Method) -> None:
        report = self.ctx.get_report(method.block.name)

        # --- Validate request type
        exc = self._check_type_consistency(method.request_type, "request")
        if exc:
            report.add_error(method.name, str(exc), code="E801")

        # --- Validate response type
        exc = self._check_type_consistency(method.response_type, "response")
        if exc:
            report.add_error(method.name, str(exc), code="E802")

        # --- Validate options and description
        self._check_meta(method, report)

    def _check_type_consistency(
        self, arg_type: type[Any], label: str
    ) -> Optional[Exception]:
        if arg_type is None:
            return TypeError(f"{label.capitalize()} type is None")

        if not isinstance(arg_type, type):
            return TypeError(f"{label.capitalize()} type is not a type: {arg_type}")

        if not issubclass(arg_type, BaseMessage):
            return TypeError(
                f"{label.capitalize()} type is not a BaseMessage: {arg_type}"
            )

        return None

    def _check_meta(self, method: Method, report: CompileReport) -> None:
        if not isinstance(method.description, str):
            report.add_error(
                method.name,
                f"Method '{method.name}' has invalid description type: {type(method.description).__name__}",
                code="E803",
            )

        if not isinstance(method.options, dict):
            report.add_error(
                method.name,
                f"Method '{method.name}' options must be a dict. Found {type(method.options).__name__}",
                code="E804",
            )
        else:
            for k, v in method.options.items():
                if not isinstance(k, str):
                    report.add_error(
                        method.name,
                        f"Method '{method.name}' option key must be a string. Found {type(k).__name__}",
                        code="E805",
                    )
                if not isinstance(v, (str, bool)):
                    report.add_error(
                        method.name,
                        f"Method '{method.name}' option value must be string or bool. Found {type(v).__name__}",
                        code="E806",
                    )
