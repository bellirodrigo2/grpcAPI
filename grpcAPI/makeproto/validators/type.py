import inspect
from typing import Any, Callable, List, Optional, get_args, get_origin

from grpcAPI.makeproto.compiler import CompilerPass
from grpcAPI.makeproto.protoblock import Block, EnumField, Field, Method
from grpcAPI.makeproto.report import CompileErrorCode, CompileReport
from grpcAPI.types import (
    DEFAULT_PRIMITIVES,
    BaseMessage,
    allowed_map_key,
    if_stream_get_type,
    is_BaseMessage,
)
from grpcAPI.types.message import BaseEnum
from grpcAPI.types.types import BaseField


def is_async_func(func: Callable[..., Any]) -> bool:
    return inspect.isasyncgenfunction(func)


class TypeValidator(CompilerPass):

    def __init__(
        self,
        convert_args: Optional[Callable[[List[type[Any]]], List[type[Any]]]] = None,
    ) -> None:
        super().__init__()
        self.convert_args = convert_args
        # self.extra_args: Optional[List[type[Any]]] = extra_args

    def set_default(self) -> None:
        # if self.extra_args is None:
        if self.convert_args is None:
            settings = self.ctx.settings
            self.convert_args = settings.get("convert_args", lambda x: x)

    def visit_block(self, block: Block) -> None:
        for field in block.fields:
            field.accept(self)

    def visit_field(self, field: Field) -> None:
        report = self.ctx.get_report(field.top_block.name)
        error: Optional[str] = None
        if isinstance(field, EnumField):
            if field.ftype:
                error = f"EnumField should have empty ftype. Found {field.ftype}"
        else:
            error = self._check_arg(field.ftype, field.name)
        if error:
            report.report_error(
                code=CompileErrorCode.FIELD_TYPE_INVALID,
                location=field.name,
                override_msg=str(error),
            )

    def _check_arg(self, bt: Optional[type[Any]], name: str) -> Optional[str]:
        if bt is None:
            return f'Field "{name}" has no type annotation'

        origin = get_origin(bt)
        args = get_args(bt)

        if origin is list:
            return self._check_type(args[0], name)

        if origin is dict:
            key_type, val_type = args
            if key_type in allowed_map_key:
                return self._check_type(val_type, name)
            return f'Field "{name}" is a dict with not allowed key type. Found "{key_type}" as dict key'

        return self._check_type(bt, name)

    def _check_type(self, bt: Any, name: str) -> Optional[str]:
        # bt pode ser qualquer coisa
        if not isinstance(bt, type):
            return f'Field "{name}" is not a type. Found {bt}'

        if issubclass(bt, BaseField):  # se for mensagem protobuf pura
            return None

        if issubclass(bt, BaseMessage) or issubclass(
            bt, BaseEnum
        ):  # se for mensagem protobuf pura
            try:
                bt.protofile()
                return None
            except NotImplementedError:
                return f"Message or Enum class '{bt.__name__}' does not implement protofile()"

        if bt not in DEFAULT_PRIMITIVES:
            return f'Field "{name}" type is not allowed. Found {bt.__name__}'

        return None

    def _check_requests(
        self, name: str, report: CompileReport, requests: List[type[Any]]
    ) -> None:
        msg = None
        invalid_req = CompileErrorCode.METHOD_INVALID_REQUEST_TYPE
        if len(requests) == 0:
            msg = "Method must define a request message."
        elif len(requests) > 1:
            msg = f"Only one request message allowed per method. Found {len(requests)}"
        elif not is_BaseMessage(requests[0]):
            msg = invalid_req.description
        if msg is not None:
            report.report_error(code=invalid_req, location=name, override_msg=msg)

    def _check_response(self, method: Method) -> None:
        report: CompileReport = self.ctx.get_report(method.block.name)
        if not is_BaseMessage(method.response_type):
            report.report_error(
                CompileErrorCode.METHOD_INVALID_RESPONSE_TYPE, location=method.name
            )
        if if_stream_get_type(method.response_type):
            if not is_async_func(method.method_func):
                report.report_error(
                    code=CompileErrorCode.METHOD_RETURN_STREAM_IS_NOT_ASYNC_GENERATOR,
                    location=method.name,
                )

    def visit_method(self, method: Method) -> None:
        report: CompileReport = self.ctx.get_report(method.block.name)
        if method.request_type is None:
            report.report_error(
                CompileErrorCode.METHOD_INVALID_REQUEST_TYPE,
                location=method.name,
                override_msg='Request type is "None"',
            )
        else:
            requests = self.convert_args(method.request_type)
            self._check_requests(method.name, report, requests)

        if method.response_type is None:
            report.report_error(
                CompileErrorCode.METHOD_INVALID_RESPONSE_TYPE,
                location=method.name,
                override_msg="Response type is 'None'",
            )
        else:
            self._check_response(method)
