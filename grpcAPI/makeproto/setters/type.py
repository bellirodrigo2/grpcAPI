from typing import Any, Tuple, get_args, get_origin

from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.protoblock import Block, Field, Method
from grpcAPI.makeproto.report import CompileErrorCode, CompileReport
from grpcAPI.types import DEFAULT_PRIMITIVES, BaseProto, if_stream_get_type
from grpcAPI.types.message import BaseEnum, BaseMessage
from grpcAPI.types.types import BaseField


def get_base_type_str(bt: type[BaseProto], block_package: str) -> str:

    if bt is None:
        return ""

    if issubclass(bt, BaseMessage) or issubclass(bt, BaseEnum):
        if bt.package() == block_package:
            return bt.prototype()
        else:
            return bt.qualified_prototype()
    if issubclass(bt, BaseField):
        return bt.prototype()

    primitive = DEFAULT_PRIMITIVES.get(bt, None)  # type: ignore
    if primitive is not None:
        return primitive.prototype()
    raise ValueError(f"{bt} object of type {type(bt)} cannot be resolved")


def get_type_str(bt: type[Any], block_package: str) -> str:
    origin = get_origin(bt)
    args = get_args(bt)

    if origin is list:
        type_str = get_base_type_str(args[0], block_package)
        return f"repeated {type_str}"

    if origin is dict:
        key_type, value_type = args
        key_type_str = get_base_type_str(key_type, block_package)
        value_type_str = get_base_type_str(value_type, block_package)
        return f"map<{key_type_str}, {value_type_str}>"
    return get_base_type_str(bt, block_package)


def get_func_arg_info(tgt: type[Any]) -> Tuple[type[Any], bool]:
    argtype = if_stream_get_type(tgt)
    if argtype is not None:
        return argtype, True
    return tgt, False


class TypeSetter(CompilerPass):

    def visit_block(self, block: Block) -> None:
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        block = field.block
        try:
            render_dict = field.render_dict
            type_str = get_type_str(field.ftype, block.package)
            render_dict["ftype"] = type_str
        except Exception as e:
            report: CompileReport = self.ctx.get_report(field.block.name)
            report.report_error(
                CompileErrorCode.SETTER_PASS_ERROR,
                field.name,
                f"TypeSetter.visit_field: {str(e)}",
            )

    def visit_method(self, method: Method) -> None:
        try:
            render_dict = method.render_dict
            request_type, request_stream = get_func_arg_info(method.request_type[0])
            request_str = get_type_str(request_type, method.block.package)
            render_dict["request_type"] = request_str
            render_dict["request_stream"] = request_stream
            response_type, response_stream = get_func_arg_info(method.response_type)
            response_str = get_type_str(response_type, method.block.package)
            render_dict["response_type"] = response_str
            render_dict["response_stream"] = response_stream
        except Exception as e:
            report: CompileReport = self.ctx.get_report(method.block.name)
            report.report_error(
                CompileErrorCode.SETTER_PASS_ERROR,
                method.name,
                f"TypeSetter.visit_method: {str(e)}",
            )
