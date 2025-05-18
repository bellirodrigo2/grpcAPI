from grpcAPI.proto_proxy import ProtoProxy
from grpcAPI.types.message import BaseMessage


class ProtoModel(BaseMessage, ProtoProxy):
    pass
