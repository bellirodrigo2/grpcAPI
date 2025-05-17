from typing import Any, Dict, List, Optional

from rich.console import Console

from grpcAPI.makeproto.block_models import Block, Field, Method, Visitor
from grpcAPI.makeproto.compiler.report import CompileReport


class CompilerContext:
    def __init__(
        self,
        blocks: List[Block],
        settings: Optional[Dict[str, Any]] = None,
        state: Optional[Dict[str, Any]] = None,
    ):
        self.blocks = blocks
        self.settings = settings or {}
        self.reports: Dict[str, CompileReport] = {
            block.name: CompileReport(name=block.name) for block in blocks
        }
        self.state = state or {}

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


class CompilerPass(Visitor):
    def __init__(self) -> None:
        self._ctx: CompilerContext | None = None

    def execute(self, blocks: list[Block], ctx: CompilerContext) -> None:
        self._ctx = ctx
        for block in blocks:
            block.accept(self)

    @property
    def ctx(self) -> CompilerContext:
        if self._ctx is None:
            raise RuntimeError(
                "CompilerContext not set. Did you forget to call `.execute()`?"
            )
        return self._ctx

    def visit_block(self, block: Block) -> None: ...

    def visit_field(self, field: Field) -> None: ...

    def visit_method(self, method: Method) -> None: ...


def compile_proto(
    blocks: list[Block],
    passes: list[CompilerPass],
    settings: Optional[Dict[str, Any]] = None,
) -> CompilerContext:

    ctx = CompilerContext(blocks, settings)

    for p in passes:
        p.execute(blocks, ctx)

    return ctx
