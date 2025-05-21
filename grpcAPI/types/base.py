from typing import Any, Dict, Optional, Union


class EnumValue(str):
    pass


class ProtoOption(Dict[str, Union[str, bool, EnumValue]]):
    pass


class BaseProto:

    @classmethod
    def prototype(cls) -> str:
        raise NotImplementedError(
            f"prototype() must be implemented by the subclass. Not implemented for: {cls.__name__}"
        )

    @classmethod
    def qualified_prototype(cls) -> str:
        raise NotImplementedError(
            "qualified_prototype() must be implemented by the subclass. Not implemented for: {cls.__name__}"
        )


class Metadata:
    def __init__(
        self,
        description: str = "",
        options: Optional[ProtoOption] = None,
        index: Optional[int] = None,
        **meta: Any,
    ) -> None:
        self.description = description
        self.options = options or ProtoOption()
        self.index = index
        self.meta = meta


class OneOf(Metadata):
    def __init__(
        self,
        key: str,
        description: str = "",
        options: Optional[ProtoOption] = None,
        index: Optional[int] = None,
        **meta: Any,
    ):
        self.key = key
        super().__init__(description, options, index, **meta)
