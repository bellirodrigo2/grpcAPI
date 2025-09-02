from typing import Any, Dict, Tuple

from google.protobuf import descriptor_pb2, descriptor_pool

from grpcAPI.makeproto.interface import IService
from grpcAPI.service_proc import ProcessService


class RegisterDescriptors(ProcessService):

    def __init__(self, **kwargs: Any) -> None:
        self.fds: Dict[Tuple[str, str], descriptor_pb2.FileDescriptorProto] = {}
        self.pool = descriptor_pool.Default()

    def _is_registered(self, filename: str) -> bool:
        try:
            self.pool.FindFileByName(filename)
            return True
        except KeyError:
            return False

    def _get_fd(self, label: Tuple[str, str]) -> descriptor_pb2.FileDescriptorProto:

        fd = self.fds.get(label)
        if fd is None:
            fd = descriptor_pb2.FileDescriptorProto()
            fd.name, fd.package = label
            self.fds[label] = fd
        return fd

    def _process_service(self, service: IService) -> None:

        label = (f"_{service.module}_", service.package)
        fd = self._get_fd(label)
        register_service(fd, service)

    def stop(self) -> None:
        for fd in self.fds.values():
            if not self._is_registered(fd.name):
                self.pool.Add(fd)
        self.fds.clear()


def register_service(fd: descriptor_pb2.FileDescriptorProto, service: IService) -> None:
    fdservice = fd.service.add()
    fdservice.name = service.name

    for method in service.methods:
        rpc = fdservice.method.add()
        rpc.name = method.name

        rpc.input_type = f".{method.input_base_type.DESCRIPTOR.full_name}"
        rpc.output_type = f".{method.output_base_type.DESCRIPTOR.full_name}"
        rpc.client_streaming = method.is_client_stream
        rpc.server_streaming = method.is_server_stream
