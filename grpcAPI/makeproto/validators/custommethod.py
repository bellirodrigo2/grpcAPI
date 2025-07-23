from typing import Any, Callable, List, Optional

from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.report import CompileErrorCode
from grpcAPI.makeproto.template import MethodTemplate, ServiceTemplate


class CustomPass(CompilerPass):
    def __init__(
        self,
        visitmethod: Callable[[Callable[..., Any]], List[str]],
        reset: Optional[Callable[[Any], None]] = None,
        setdefault: Optional[Callable[[Any], None]] = None,
        finish: Optional[Callable[[Any], None]] = None,
    ) -> None:
        super().__init__()
        self._visit_method = visitmethod
        self._reset = reset
        self._set_default = setdefault
        self._finish = finish

    def reset(self) -> None:
        if self._reset is not None:
            self._reset(self)

    def set_default(self) -> None:
        if self._set_default is not None:
            self._set_default(self)

    def finish(self) -> None:
        if self._finish is not None:
            self._finish(self)

    def _report(self, error_msg: List[str], method: MethodTemplate) -> None:
        report = self.ctx.get_report(block_name=method.service)
        for error in error_msg:
            report.report_error(
                CompileErrorCode.RUNTIME_POSSIBLE_ERROR, method.name, error
            )

    def visit_service(self, block: ServiceTemplate) -> None:
        for field in block.methods:
            field.accept(self)

    def visit_method(self, method: MethodTemplate) -> None:
        error_msg = self._visit_method(method.method_func)
        self._report(error_msg, method)
