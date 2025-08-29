from typing import Any, Dict

from grpcAPI.makeproto.interface import ILabeledMethod
from grpcAPI.process_service import ProcessService


def proto_http_option(mapping: Dict[str, Any]) -> str:
    def format_value(v: Any) -> str:
        if isinstance(v, str):
            return f'"{v}"'
        elif isinstance(v, bool):
            return "true" if v else "false"
        elif isinstance(v, (int, float)):
            return str(v)
        elif isinstance(v, dict):
            return (
                "{ "
                + " ".join(f"{k}: {format_value(val)}" for k, val in v.items())
                + " }"
            )
        elif isinstance(v, (list, tuple)):
            return "[ " + ", ".join(format_value(i) for i in v) + " ]"
        else:
            raise TypeError(f"Non Supported type for value '{v}': {type(v)}")

    lines = [f"  {k}: {format_value(v)}" for k, v in mapping.items()]
    return f"(google.api.http) = {{\n" + "\n".join(lines) + "\n}}"


class AddGateway(ProcessService):

    def __init__(self, **kwargs: Any) -> None:
        self.word = "gateway"
        self.errors = []

    def _process_method(self, method: ILabeledMethod) -> None:

        if self.word in method.meta:
            try:
                option_str = proto_http_option(method.meta[self.word])
                method.options.append(option_str)
            except ValueError as e:
                # add to errors
                pass

    def stop(self) -> None:
        if self.errors:
            pass
