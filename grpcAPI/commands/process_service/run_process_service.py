from typing import Any, Callable, Dict, List, Optional

from grpcAPI.app import App
from grpcAPI.commands.process_service import ProcessService
from grpcAPI.commands.process_service.format_service import FormatService
from grpcAPI.commands.process_service.inject_typing import InjectProtoTyping


def run_process_service(
    app: App,
    settings: Dict[str, Any],
    process_service_cls: Optional[List[Callable[..., ProcessService]]] = None,
) -> None:

    process_service_cls = process_service_cls or []
    process_service_cls.append(FormatService)
    process_service_cls.append(InjectProtoTyping)
    process_services = [
        proc_service(**settings) for proc_service in set(process_service_cls)
    ]
    for service in app.service_list:
        for proc in process_services:
            proc.process(service)
