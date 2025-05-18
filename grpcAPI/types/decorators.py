from typing import Dict, List, Optional, Union

from grpcAPI.types.base import ProtoOption


class ProtoModule:
    def __init__(self, profile: str, package: str = ""):
        self.profile = profile
        self.package_name = package

    def __call__(self, cls: type) -> type:
        cls.protofile = classmethod(lambda cls_: self.profile)
        cls.package = classmethod(lambda cls_: self.package_name)
        cls.prototype = classmethod(lambda cls_: cls_.__name__)
        cls.qualified_prototype = classmethod(
            lambda cls_: f"{cls.package()}.{cls.__name__}"
        )

        cls.description = classmethod(lambda cls_: "")
        cls.options = classmethod(lambda cls_: ProtoOption())
        cls.reserved_index = classmethod(lambda cls_: [])

        return cls


class ProtoHeader:
    def __init__(
        self,
        description: str = "",
        options: Optional[Dict[str, Union[str, bool]]] = None,
        reserved_index: Optional[List[Union[int, range]]] = None,
    ):
        self.description = description
        self.options = ProtoOption(**(options or {}))
        self.reserved_index = reserved_index or []

    def __call__(self, cls: type) -> type:
        cls.description = classmethod(lambda cls_: self.description)
        cls.options = classmethod(lambda cls_: self.options)
        cls.reserved_index = classmethod(lambda cls_: self.reserved_index)
        return cls
