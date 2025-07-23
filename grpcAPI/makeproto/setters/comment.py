from typing_extensions import Callable

from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.template import MethodTemplate, ProtoTemplate, ServiceTemplate


class CommentSetter(CompilerPass):
    def __init__(self, format: Callable[[str], str] = lambda x: x):
        super().__init__()
        self.format = format

    def visit_service(self, block: ServiceTemplate) -> None:
        module: ProtoTemplate = self.ctx.get_state(block.module)
        module.comments = self.format(module.comments)
        block.comments = self.format(block.comments)
        for field in block.methods:
            field.accept(self)

    def visit_method(self, method: MethodTemplate) -> None:
        method.comments = self.format(method.comments)
