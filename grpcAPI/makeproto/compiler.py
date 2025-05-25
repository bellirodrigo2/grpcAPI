from typing import Any, Dict, List, Optional, Union

from rich.console import Console

from grpcAPI.makeproto.protoblock import Block, Field, Method, Visitor
from grpcAPI.makeproto.report import CompileReport


class CompilerContext:
    def __init__(
        self,
        name: str = "",
        settings: Optional[Dict[str, Any]] = None,
        state: Optional[Dict[Union[str, object], Any]] = None,
    ):
        self.name = name
        self.settings: Dict[str, Any] = settings or {}
        self.reports: Dict[str, CompileReport] = {}
        self._state: Dict[Union[str, object], Any] = state or {}

    def __len__(self) -> int:
        return sum(len(r) for r in self.reports.values())

    def get_state(self, key: str) -> Optional[Any]:
        return self._state.get(key, None)

    def get_report(self, block_name: str) -> CompileReport:
        if block_name not in self.reports:
            self.reports[block_name] = CompileReport(name=block_name)
        return self.reports[block_name]

    def is_valid(self) -> bool:
        return all(report.is_valid() for report in self.reports.values())

    def show(self) -> None:
        console = Console()
        for name, report in self.reports.items():
            if len(report) > 0:
                console.rule(f"[bold red]Block: {name}")
                report.show()
        if self.is_valid():
            console.print("[green bold]✓ All blocks compiled successfully!")


def list_ctx_error(context: CompilerContext) -> List[str]:
    return [err.code for report in context.reports.values() for err in report.errors]


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

    def execute(self, blocks: list[Block], ctx: CompilerContext) -> None:
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
            )
        return self._ctx

    def visit_block(self, block: Block) -> None:
        return

    def visit_field(self, field: Field) -> None:
        return

    def visit_method(self, method: Method) -> None:
        return


def compile_proto(
    blocks: list[Block],
    passes: list[CompilerPass],
    ctx: CompilerContext,
    # settings: Optional[Dict[str, Any]] = None,
) -> CompilerContext:

    for p in passes:
        p.execute(blocks, ctx)

    return ctx
