from typing import Dict, Set, Union

from grpcAPI.makeproto.block_models import Block
from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.protoobj.message import NO_PACKAGE


class PackageConsistencyValidator(CompilerPass):
    def __init__(self) -> None:
        super().__init__()
        self.protofile_packages: Dict[str, Set[Union[str, object]]] = {}

    def visit_block(self, block: Block) -> None:
        protofile = block.protofile
        package = block.package if block.package else NO_PACKAGE

        if protofile not in self.protofile_packages:
            self.protofile_packages[protofile] = set()
        self.protofile_packages[protofile].add(package)

    def finalize(self) -> None:
        for protofile, packages in self.protofile_packages.items():
            if len(packages) > 1:
                ctx = self.ctx
                report = ctx.get_report(f"<protofile::{protofile}>")

                def _pkg_label(p: str) -> str:
                    return "<no package>" if p is NO_PACKAGE else p

                pkg_names = sorted(_pkg_label(p) for p in packages)

                report.add_error(
                    location=protofile,
                    message=f'Protofile "{protofile}" has inconsistent packages: {", ".join(pkg_names)}',
                    code="E701",
                )
