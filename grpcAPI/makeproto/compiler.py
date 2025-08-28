from rich.console import Console
from typing_extensions import Any, Dict, List, Optional

from grpcAPI.makeproto.report import CompileReport
from grpcAPI.makeproto.template import MethodTemplate, ServiceTemplate, Visitor


class CompilerContext:
    def __init__(
        self,
        name: str = "",
        state: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.reports: Dict[Any, CompileReport] = {}
        self._state: Dict[str, Any] = state or {}

    def __len__(self) -> int:
        return sum(len(r) for r in self.reports.values())

    def has_errors(self) -> bool:
        return any(not report.is_valid() for report in self.reports.values())

    def get_state(self, key: str) -> Optional[Any]:
        return self._state.get(key)

    def get_report(self, block_name: Any) -> CompileReport:
        if block_name not in self.reports:
            self.reports[block_name] = CompileReport(name=block_name.name)
        return self.reports[block_name]

    def is_valid(self) -> bool:
        return all(report.is_valid() for report in self.reports.values())

    def show(self) -> None:
        console = Console()
        for name, report in self.reports.items():
            if len(report) > 0:
                console.rule(f"[bold red]Package: {name.name}")
                report.show()
        if self.is_valid():
            console.print("[green bold]✓ All blocks compiled successfully!")


def list_ctx_error_messages(context: CompilerContext) -> List[str]:
    return [err.message for report in context.reports.values() for err in report.errors]


def list_ctx_error_code(context: CompilerContext) -> List[str]:
    return [err.code for report in context.reports.values() for err in report.errors]


class CompilerPass(Visitor):
    def __init__(self) -> None:
        self._ctx: Optional[CompilerContext] = None

    def reset(self) -> None:
        pass

    def set_default(self) -> None:
        pass

    def finish(self) -> None:
        pass

    def execute(self, blocks: List[ServiceTemplate], ctx: CompilerContext) -> None:
        self._ctx = ctx
        self.set_default()
        for block in blocks:
            block.accept(self)
            self.reset()
        self.finish()

    @property
    def ctx(self) -> CompilerContext:
        if self._ctx is None:
            raise RuntimeError(
                "CompilerContext not set. Did you forget to call `.execute()`?"
            )  # pragma: no cover
        return self._ctx

    def visit_service(self, block: ServiceTemplate) -> None:
        return  # pragma: no cover

    def visit_method(self, method: MethodTemplate) -> None:
        return  # pragma: no cover
