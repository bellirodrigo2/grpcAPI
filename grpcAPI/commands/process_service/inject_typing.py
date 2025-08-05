from typing import Any, Sequence

from grpcAPI.commands.process_service import ProcessService
from grpcAPI.makeproto.interface import ILabeledMethod, IMetaType
from grpcAPI.protobut_typing import inject_proto_typing


class InjectProtoTyping(ProcessService):

    def __init__(self, **kwargs: Any) -> None:
        pass

    def _process_method(self, method: ILabeledMethod) -> None:
        requests: Sequence[IMetaType] = method.request_types

        for model in requests:
            inject_proto_typing(model.basetype)
