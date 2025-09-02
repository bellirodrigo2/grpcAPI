from typing import Any, Callable, Dict, List, Optional

from grpcAPI.app import App
from grpcAPI.service_proc import ProcessService

# from grpcAPI.service_proc.add_gateway import AddGateway
from grpcAPI.service_proc.filter_service import DisableService

# from grpcAPI.service_proc.format_service import FormatService
from grpcAPI.service_proc.inject_typing import InjectProtoTyping

# from grpcAPI.service_proc.register_descriptor import RegisterDescriptors


def run_process_service(
    app: App,
    settings: Dict[str, Any],
    process_service_cls: Optional[List[Callable[..., ProcessService]]] = None,
) -> None:

    process_service_cls = process_service_cls or []
    # process_service_cls.append(FormatService)  # build
    process_service_cls.append(InjectProtoTyping)  # all
    process_service_cls.append(DisableService)  # all
    # process_service_cls.append(RegisterDescriptors)  # run
    # process_service_cls.append(AddGateway)  # build
    process_services = [
        proc_service(**settings) for proc_service in set(process_service_cls)
    ]
    for proc in process_services:
        proc.start(app.name, app.version)
        for service in app.service_list:
            proc.process(service)
        proc.close()
