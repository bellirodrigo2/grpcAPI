from typing import Any, Callable, List, Optional

from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.compiler.report import CompileErrorCode
from grpcAPI.makeproto.protoblock import Method


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

    def _report(self, error_msg: List[str], name: str) -> None:
        report = self.ctx.get_report(block_name=name)
        for error in error_msg:
            report.report_error(CompileErrorCode.RUNTIME_POSSIBLE_ERROR, name, error)

    def visit_method(self, method: Method) -> None:
        error_msg = self._visit_method(method.method_func)
        self._report(error_msg, method.name)
