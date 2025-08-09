from typing import Sequence

from grpcAPI.makeproto.interface import ILabeledMethod, IMetaType
from grpcAPI.process_service import ProcessService
from grpcAPI.protobut_typing import inject_proto_typing


class InjectProtoTyping(ProcessService):

    def _process_method(self, method: ILabeledMethod) -> None:
        requests: Sequence[IMetaType] = method.request_types

        for model in requests:
            inject_proto_typing(model.basetype)
