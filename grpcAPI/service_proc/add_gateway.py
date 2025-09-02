from collections import defaultdict
from typing import Any, Dict

from grpcAPI.makeproto.interface import ILabeledMethod, IService
from grpcAPI.service_proc import ProcessService


def proto_http_option(mapping: Dict[str, Any]) -> str:
    def format_value(v: Any) -> str:
        if isinstance(v, str):
            return f'"{v}"'
        elif isinstance(v, bool):
            return "true" if v else "false"
        elif isinstance(v, (int, float)):
            return str(v)
        elif isinstance(v, dict):
            items = [f"{k}: {format_value(val)}" for k, val in v.items()]
            return "{ " + " ".join(items) + " }"
        elif isinstance(v, (list, tuple)):
            items = [format_value(i) for i in v]
            return "[ " + ", ".join(items) + " ]"
        else:
            raise ValueError(f"Unsupported type for value '{v}': {type(v)}")

    lines = [f"    {k}: {format_value(v)}" for k, v in mapping.items()]
    return f"(google.api.http) = {{\n" + "\n".join(lines) + "\n  }"


class AddGateway(ProcessService):

    def __init__(self, **kwargs: Any) -> None:
        self.word = "gateway"
        self.errors = defaultdict(list)
        self.current_service = None

    def _process_service(self, service: IService) -> None:
        self.current_service = service

    def _process_method(self, method: ILabeledMethod) -> None:
        if self.word in method.meta:
            if self.current_service is None:
                raise ValueError("Current service is not set.")
            self.current_service.module_level_imports.append(
                "google/api/annotations.proto"
            )
            self.current_service.module_level_imports.append("google/api/http.proto")
            try:
                option_str = proto_http_option(method.meta[self.word])
                method.options.append(option_str)
            except ValueError as e:
                self.errors[method.name].append(str(e))

    def close(self) -> None:
        if self.errors:
            error_msg = "Gateway option errors: " + str(dict(self.errors))
            raise ValueError(error_msg)
