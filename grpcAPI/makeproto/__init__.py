from grpcAPI.makeproto.interface import (
    ILabeledMethod,
    IMetaType,
    IProtoPackage,
    IService,
)

__all__ = [
    "compile_service",
    "IService",
    "ILabeledMethod",
    "IMetaType",
    "IProtoPackage",
]

from grpcAPI.makeproto.build_service import compile_service
