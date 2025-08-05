from grpcAPI.makeproto import IService
from grpcAPI.makeproto.interface import ILabeledMethod


class ProcessService:

    def _process_service(self, service: IService) -> None:
        pass

    def _process_method(self, method: ILabeledMethod) -> None:
        pass

    def process(self, service: IService) -> None:
        self._process_service(service)
        for method in service.methods:
            self._process_method(method)
