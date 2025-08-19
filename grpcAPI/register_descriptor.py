from typing import Dict, Iterable, Tuple

from google.protobuf import descriptor_pb2, descriptor_pool

from grpcAPI.makeproto.interface import IService


def register_service_descriptors(services: Iterable[IService]) -> None:
    reg_desc = RegisterDescriptors()
    for service in services:
        reg_desc.add_service(service)
    reg_desc.register()


class RegisterDescriptors:

    def __init__(self) -> None:
        self.fds: Dict[Tuple[str, str], descriptor_pb2.FileDescriptorProto] = {}
        self.pool = descriptor_pool.Default()

    def is_registered(self, filename: str) -> bool:
        try:
            self.pool.FindFileByName(filename)
            return True
        except KeyError:
            return False

    def _get_fd(self, label: Tuple[str, str]) -> descriptor_pb2.FileDescriptorProto:

        fd = self.fds.get(label, None)
        if fd is None:
            fd = descriptor_pb2.FileDescriptorProto()
            fd.name, fd.package = label
            self.fds[label] = fd
        return fd

    def add_service(self, service: IService) -> None:

        label = (f"_{service.module}_", service.package)
        fd = self._get_fd(label)
        register_service(fd, service)

    def register(self) -> None:
        for fd in self.fds.values():
            if not self.is_registered(fd.name):
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
