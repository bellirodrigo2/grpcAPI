from datetime import datetime
from typing import Any

import pytest
from typemapping import get_func_args
from typing_extensions import Annotated, Dict, List

from grpcAPI.makeproto_pass import validate_signature_pass
from grpcAPI.types import Depends, FromRequest
from grpcAPI.validators import BaseValidator

# from grpcAPI.validators import ctxinject_inject_validation, inject_typing
from grpcAPI.validators.inject_pydantic_validation import PydanticValidator
from grpcAPI.validators.inject_validation import StdValidator
from tests.conftest import (
    ClassMsg,
    InnerMessage,
    Other,
    Struct,
    Timestamp,
    User,
    UserCode,
)


@pytest.mark.parametrize("validator", [StdValidator(), PydanticValidator()])
def test_inject_typing(validator) -> None:

    User.__annotations__ = {}

    async def get_db() -> str:
        return "sqlite"

    def func(
        other: Annotated[Other, FromRequest(User)],
        code: UserCode = FromRequest(User),
        age: InnerMessage = FromRequest(User),
        time: datetime = FromRequest(User),
        name: str = FromRequest(User),
        employee: str = FromRequest(User),
        inactive: bool = FromRequest(User),
        others: List[Other] = FromRequest(User),
        dict: Dict[str, str] = FromRequest(User),
        msg: ClassMsg = FromRequest(User),
        map_msg: Dict[int, InnerMessage] = FromRequest(User),
        code2: UserCode = FromRequest(User, field="code"),
        codes: List[UserCode] = FromRequest(User),
        db: str = Depends(get_db),
    ) -> None:
        pass

    errors = validate_signature_pass(func, list(validator.casting_list))
    assert errors == []


@pytest.mark.parametrize("validator", [StdValidator(), PydanticValidator()])
def test_validate_date(validator) -> None:

    def func(
        time: datetime = FromRequest(
            User, start=datetime(2023, 6, 6), end=datetime(2025, 6, 6)
        ),
    ) -> None:
        return

    args = get_func_args(func)
    modelinj = args[0].getinstance(FromRequest)
    assert not modelinj.has_validate
    validator.inject_validation(func)
    assert modelinj.has_validate

    ts = Timestamp()
    ts.FromDatetime(datetime(2024, 6, 6))
    assert modelinj.validate(ts, basetype=datetime) == datetime(2024, 6, 6)

    with pytest.raises(ValueError):
        ts = Timestamp()
        ts.FromDatetime(datetime(2022, 6, 6))
        assert modelinj.validate(ts, basetype=datetime) == datetime(2024, 6, 6)

    with pytest.raises(ValueError):
        ts = Timestamp()
        ts.FromDatetime(datetime(2026, 6, 6))
        assert modelinj.validate(ts, basetype=datetime) == datetime(2024, 6, 6)


@pytest.mark.parametrize("validator", [StdValidator(), PydanticValidator()])
def test_validate_struct(validator) -> None:

    def func(
        dict: Dict[str, Any] = FromRequest(User, min_length=1, max_length=2),
    ) -> None:
        return

    args = get_func_args(func)
    modelinj = args[0].getinstance(FromRequest)
    assert not modelinj.has_validate
    validator.inject_validation(func)
    assert modelinj.has_validate

    struct = Struct()
    bdict = {"foo": "bar"}
    struct.update(bdict)
    assert modelinj.validate(struct, basetype=None) == bdict

    with pytest.raises(ValueError):
        struct.update({"hello": "world", "key": "val"})
        assert modelinj.validate(struct, basetype=None)

    with pytest.raises(ValueError):
        struct = Struct()
        struct.update({})
        modelinj.validate(struct, basetype=None)
