from typing_extensions import Protocol

from grpcAPI.makeproto import IService


class ProcessService(Protocol):

    def __call__(self, service: IService) -> None: ...
