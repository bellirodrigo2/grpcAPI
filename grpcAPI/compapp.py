from typing import Any, List, Set, Tuple

from grpcAPI.app import App, Package, map_package_block
from grpcAPI.makeproto.compiler.compiler import CompilerContext
from grpcAPI.makeproto.protoblock import Block


def compile_app(app: App, ignore_instance: List[type[Any]]) -> None:

    packages: List[Package] = list(app.packages.values())
    packset: Set[Tuple[str, str]] = set()
    for pack in packages:
        for mod in pack:
            packset.add(pack.packname, mod.modname)

    state = {"_packages": packset}

    #tem que rodar type validator antes de imports validator

    for pack in packages:
        
