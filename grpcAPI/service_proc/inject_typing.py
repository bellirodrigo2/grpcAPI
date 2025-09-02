from typing_extensions import Sequence

from grpcAPI.makeproto.interface import ILabeledMethod, IMetaType
from grpcAPI.service_proc import ProcessService
from grpcAPI.typehint_proto import inject_proto_typing


class InjectProtoTyping(ProcessService):

    def _process_method(self, method: ILabeledMethod) -> None:
        requests: Sequence[IMetaType] = method.request_types

        for model in requests:
            inject_proto_typing(model.basetype)
