from makeproto import IService
from typing_extensions import Protocol


class ProcessService(Protocol):

    def __call__(self, service: IService) -> None: ...
