from typing import Dict, Tuple

from google.protobuf import descriptor_pb2, descriptor_pool

from grpcAPI.makeproto.interface import IService


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

        label = (service.module, service.package)
        fd = self._get_fd(label)
        register_service(fd, service)

    def register(self) -> None:

        # pool.Add(file_desc_proto)

        pass


def register_service(fd: descriptor_pb2.FileDescriptorProto, service: IService) -> None:

    fdservice = fd.service.add()
    fdservice.name = service.name

    for method in service.methods:
        rpc = fdservice.method.add()
        rpc.name = method.name
        rpc.input_type = method.input_type.__name__
        rpc.output_type = method.output_type.__name__
        rpc.client_streaming = method.is_client_stream
        rpc.server_streaming = method.is_server_stream
