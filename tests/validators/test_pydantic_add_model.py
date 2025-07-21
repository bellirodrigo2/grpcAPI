import asyncio
import json
from typing import Any, Callable, Dict, Type

import orjson
import pytest
from ctxinject.inject import get_mapped_ctx, resolve_mapped_ctx
from pydantic import BaseModel, Field, ValidationError
from typing_extensions import Annotated

from grpcAPI.types import FromRequest
from grpcAPI.validators.inject_pydantic_validation import PydanticValidator
from tests.conftest import BytesValue, StringValue


@pytest.fixture
def validator() -> PydanticValidator:
    return PydanticValidator()


class Model1(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=3)]
    age: Annotated[int, Field(ge=18, le=80)]


@pytest.mark.parametrize(
    "type_,convert,model",
    [(str, json.dumps, StringValue), (bytes, orjson.dumps, BytesValue)],
)
def test_validate_str(
    type_: Type[Any],
    convert: Callable[[Any], str],
    model: Type[Any],
    validator: PydanticValidator,
) -> None:

    def func_model1(
        value: Model1 = FromRequest(model),
    ) -> Model1:
        return value

    assert (type_, Model1) not in validator.casting_list
    validator.inject_validation(func_model1)
    assert (type_, Model1) in validator.casting_list

    def try_this(item: Dict[str, Any]) -> None:

        ser = convert(item)
        _ctx = {model: model(value=ser)}

        mapped_ctx = get_mapped_ctx(
            func=func_model1,
            context=_ctx,
            allow_incomplete=False,
            validate=True,
            overrides={},
        )

        async def run() -> None:
            kwargs = await resolve_mapped_ctx(_ctx, mapped_ctx)
            func_model1(**kwargs)

        asyncio.run(run())

    val1 = {"name": "Rod", "age": 39}
    try_this(val1)

    with pytest.raises(ValidationError):
        try_this({**val1, "name": "too_long"})

    with pytest.raises(ValidationError):
        try_this({**val1, "age": 10})
