from makeproto import IService

from grpcAPI.interfaces import ProcessService


class FilterService(ProcessService):

    def __call__(self, service: IService) -> None: ...
