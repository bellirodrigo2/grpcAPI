from typing import List, Optional

import pytest

from grpcAPI.label_method import LabeledMethod, MetaType
from grpcAPI.make_method import make_method_async


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
    with pytest.raises(ValueError):
        make_method_async(lbl_method, {}, {})


def test_make_method_no_response() -> None:
    lbl_method = make_labeled_method([str], None)
    with pytest.raises(AttributeError):
        make_method_async(lbl_method, {}, {})
