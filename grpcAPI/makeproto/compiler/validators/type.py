import inspect
from collections.abc import AsyncGenerator as ABCAsyncGenerator
from enum import Enum
from typing import Annotated, Any, Callable, List, Optional, get_args, get_origin

from grpcAPI.makeproto.block_models import Block, Method
from grpcAPI.makeproto.compiler.compiler import CompilerPass, Field
from grpcAPI.makeproto.compiler.report import CompileErrorCode, CompileReport
from grpcAPI.proto_model import ProtoModel
from grpcAPI.types import Context
from grpcAPI.types.base import BaseProto
from grpcAPI.types.types import DEFAULT_PRIMITIVES, allowed_map_key

DEFAULT_EXTRA_ARGS = [Context]


def is_protomodel(tgt: type[Any]) -> bool:
    origin = get_origin(tgt)
    if origin is Annotated:
        return is_protomodel(get_args(tgt)[0])
    bt = tgt
    if origin is ABCAsyncGenerator:
        bt = get_args(tgt)[0]
    if not isinstance(bt, type):
        return False
    return issubclass(bt, ProtoModel)


def is_async_func(func: Callable[..., Any]) -> bool:
    return inspect.isasyncgenfunction(func)


class TypeValidator(CompilerPass):

    def __init__(self, extra_args: Optional[List[type[Any]]] = None) -> None:
        super().__init__()
        self.extra_args: Optional[List[type[Any]]] = extra_args

    def visit_block(self, block: Block) -> None:
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        report: CompileReport = self.ctx.get_report(field.block.name)

        if field.block.block_type == "enum":
            # Enum must have no type
            if field.ftype is not None:
                report.report_error(
                    code=CompileErrorCode.ENUM_FIELD_HAS_TYPE,
                    location=field.name,
                    override_msg=f"Enum field '{field.name}' must not have a type. Found {field.ftype}",
                )
            return

        # Non-enum: ftype must be valid
        error = self._check_arg(field.ftype, field.name)
        if error:
            report.report_error(
                code=CompileErrorCode.FIELD_TYPE_INVALID,
                location=field.name,
                override_msg=str(error),
            )

    def _check_arg(self, bt: Optional[type[Any]], name: str) -> Optional[TypeError]:
        if bt is None:
            return TypeError(f'Field "{name}" has no type annotation')

        origin = get_origin(bt)
        args = get_args(bt)

        if origin is list:
            return self._check_type(args[0], name)

        if origin is dict:
            key_type, val_type = args
            if key_type in allowed_map_key:
                return self._check_type(val_type, name)
            return TypeError(
                f'Field "{name}" is a dict with not allowed key type. Found "{key_type}" as dict key'
            )

        return self._check_type(bt, name)

    def _check_type(self, bt: Any, name: str) -> Optional[TypeError]:
        # bt pode ser qualquer coisa
        if not isinstance(bt, type):
            return TypeError(f'Field "{name}" is not a type. Found {bt}')

        if issubclass(bt, BaseProto):  # se for mensagem protobuf pura
            return None

        if issubclass(bt, Enum):
            file = getattr(bt, "protofile", None)
            pack = getattr(bt, "package", None)
            if callable(file) and callable(pack):
                return None

        if bt not in DEFAULT_PRIMITIVES:
            return TypeError(f'Field "{name}" type is not allowed. Found {bt}')

        return None

    def _set_default(self) -> None:
        if self.extra_args is None:
            settings = self.ctx.settings
            self.extra_args = settings.get("extra_args", DEFAULT_EXTRA_ARGS)

    def _check_requests(
        self, name: str, report: CompileReport, requests: List[type[Any]]
    ) -> None:
        error_code = None
        if len(requests) == 0:
            error_code = CompileErrorCode.METHOD_NO_REQUEST
        elif len(requests) > 1:
            error_code = CompileErrorCode.METHOD_TOO_MANY_REQUEST
        elif not is_protomodel(requests.pop()):
            error_code = CompileErrorCode.METHOD_INVALID_REQUEST_TYPE
        if error_code is not None:
            report.report_error(
                code=error_code,
                location=name,
            )

    def visit_method(self, method: Method) -> None:
        self._set_default()
        report: CompileReport = self.ctx.get_report(method.block.name)
        if method.request_type is None:
            report.report_error(
                CompileErrorCode.METHOD_INVALID_REQUEST_TYPE, location=method.name
            )
        else:
            requests = list(set(method.request_type) - set(self.extra_args))
            self._check_requests(method.name, report, requests)

        if not is_protomodel(method.response_type):
            report.report_error(
                CompileErrorCode.METHOD_INVALID_RESPONSE_TYPE, location=method.name
            )
        origin = get_origin(method.response_type)
        if origin is ABCAsyncGenerator:
            if not is_async_func(method.method_func):
                report.report_error(
                    code=CompileErrorCode.METHOD_RETURN_STREAM_IS_NOT_ASYNC_GENERATOR,
                    location=method.name,
                )
