from collections.abc import AsyncGenerator as ABCAsyncGenerator
from typing import Any, Tuple, get_args, get_origin

from typing_extensions import Annotated

from grpcAPI.makeproto.block_models import Block, Field, Method
from grpcAPI.makeproto.compiler.compiler import CompilerPass
from grpcAPI.makeproto.compiler.report import CompileErrorCode, CompileReport
from grpcAPI.types.base import BaseProto
from grpcAPI.types.types import DEFAULT_PRIMITIVES


def get_base_type_str(bt: type[BaseProto], block_package: str) -> str:

    pack = getattr(bt, "package", None)
    if pack is not None:
        # covers basemessage and enum
        if pack() == block_package:
            return bt.prototype()
        else:
            return bt.qualified_prototype()
    return DEFAULT_PRIMITIVES.get(bt).prototype()  # type: ignore
    # should be safe due to early validator pass


def get_type_str(bt: type[Any], block_package: str) -> str:
    origin = get_origin(bt)
    args = get_args(bt)

    if origin is Annotated:
        return get_type_str(args[0], block_package)

    if origin is list:
        type_str = get_base_type_str(args[0], block_package)
        return f"repeated {type_str}"

    if origin is dict:
        key_type, value_type = args
        key_type_str = get_base_type_str(key_type, block_package)
        value_type_str = get_base_type_str(value_type, block_package)
        return f"map<{key_type_str}, {value_type_str}>"

    return get_base_type_str(bt, block_package)


def get_func_arg_info(tgt: type[Any]) -> Tuple[str, bool]:
    origin = get_origin(tgt)
    args = get_args(tgt)
    if origin is Annotated:
        return get_func_arg_info(args[0])
    if origin is ABCAsyncGenerator:
        return args[0].__name__, True
    return tgt.__name__, True


class TypeSetter(CompilerPass):

    def visit_block(self, block: Block) -> None:
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        report: CompileReport = self.ctx.get_report(field.block.name)
        block = field.block
        try:
            render_dict = block.render_dict
            type_str = get_type_str(field.ftype, block.package)
            render_dict["ftype"] = type_str
        except Exception as e:
            report.report_error(CompileErrorCode.SETTER_PASS_ERROR, field.name, str(e))

    def visit_method(self, method: Method) -> None:
        report: CompileReport = self.ctx.get_report(method.block.name)
        block = method.block
        try:
            render_dict = block.render_dict
            request_type, request_stream = get_func_arg_info(method.request_type[0])
            render_dict["request_type"] = request_type
            render_dict["request_stream"] = request_stream
            response_type, response_stream = get_func_arg_info(method.response_type)
            render_dict["response_type"] = response_type
            render_dict["response_stream"] = response_stream
        except Exception as e:
            report.report_error(CompileErrorCode.SETTER_PASS_ERROR, method.name, str(e))
