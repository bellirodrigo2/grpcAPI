from typing import Any

from grpcAPI.service_proc import ProcessService


class CustomServiceProc(ProcessService):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
