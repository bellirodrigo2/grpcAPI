from typing import Any, Callable, Dict, List, Optional

from grpcAPI.app import App
from grpcAPI.process_service import ProcessService
from grpcAPI.process_service.filter_service import DisableService
from grpcAPI.process_service.format_service import FormatService
from grpcAPI.process_service.inject_typing import InjectProtoTyping
from grpcAPI.process_service.register_descriptor import RegisterDescriptors


def run_process_service(
    app: App,
    settings: Dict[str, Any],
    process_service_cls: Optional[List[Callable[..., ProcessService]]] = None,
) -> None:

    process_service_cls = process_service_cls or []
    process_service_cls.append(FormatService)
    process_service_cls.append(InjectProtoTyping)
    process_service_cls.append(DisableService)
    process_service_cls.append(RegisterDescriptors)
    process_services = [
        proc_service(**settings) for proc_service in set(process_service_cls)
    ]
    for proc in process_services:
        proc.start(app.name, app.version)
        for service in app.service_list:
            proc.process(service)
        proc.close()
