from grpcAPI.makeproto import IService
from grpcAPI.process_service import ProcessService


class FilterService(ProcessService):

    def __call__(self, service: IService) -> None: ...
