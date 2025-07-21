# @dataclass
# class LabeledMethod(ILabeledMethod):
#     title: str
#     name: str
#     method: Callable[..., Any]
#     package: str
#     module: str
#     service: str
#     comments: str
#     description: str
#     options: List[str]
#     tags: List[str]

#     request_types: List[IMetaType]
#     response_types: Optional[IMetaType]

from typing import List, Optional

import pytest

from grpcAPI.extract_types import MetaType
from grpcAPI.make_method import make_method_async
from grpcAPI.types import LabeledMethod


def make_labeled_method(req: List[MetaType], resp: Optional[MetaType]) -> LabeledMethod:
    return LabeledMethod(
        title="",
        name="",
        method=lambda x: x,
        module="",
        package="",
        service="",
        comments="",
        description="",
        options=[],
        tags=[],
        request_types=req,
        response_types=resp,
    )


def test_make_method_no_request() -> None:
    lbl_method = make_labeled_method([], None)
    with pytest.raises(IndexError):
        make_method_async(lbl_method, {}, {})


def test_make_method_no_response() -> None:
    lbl_method = make_labeled_method([str], None)
    with pytest.raises(AttributeError):
        make_method_async(lbl_method, {}, {})
