from dataclasses import Field

from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.protoblock import Block, Method
from grpcAPI.types.base import EnumValue, ProtoOption


def format_option(item: ProtoOption) -> str:

    key, value = item

    if isinstance(value, bool):  # type: ignore
        val_txt = "true" if value else "false"
    elif isinstance(value, (int, float)):
        val_txt = str(value)
    elif isinstance(value, EnumValue):
        val_txt = str(value)  # sem aspas
    else:
        val_txt = f'"{value}"'  # string literal

    return f"{key} = {val_txt}"


class OptionsSetter(CompilerPass):

    def visit_block(self, block: Block) -> None:
        options = format_option(block.options)
        block.render_dict["options"] = options
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        options = format_option(field.options)
        field.render_dict["options"] = options

    def visit_method(self, method: Method) -> None:
        options = format_option(method.options)
        method.render_dict["options"] = options
