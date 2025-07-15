from makeproto import IService

from grpcAPI.interfaces import ProcessService


class FormatService(ProcessService):

    def __call__(self, service: IService) -> None: ...
