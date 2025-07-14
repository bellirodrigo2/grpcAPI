from google.protobuf.timestamp_pb2 import Timestamp
from typing_extensions import Annotated, Dict, List, get_type_hints

from grpcAPI.grpcio_adaptor.makeproto_pass import validate_signature_pass
from grpcAPI.grpcio_adaptor.protobut_typing import get_type, inject_proto_typing
from grpcAPI.types import Depends, FromRequest
from tests.lib.inner.inner_pb2 import InnerMessage
from tests.lib.multi.inner.class_pb2 import ClassMsg
from tests.lib.other_pb2 import Other
from tests.lib.user_pb2 import User, UserCode


def test_fields() -> None:

    userd = User.DESCRIPTOR

    code = userd.fields_by_name["code"]
    age = userd.fields_by_name["age"]
    time = userd.fields_by_name["time"]
    affilliation = userd.fields_by_name["affilliation"]
    name = userd.fields_by_name["name"]
    other = userd.fields_by_name["other"]
    employee = userd.fields_by_name["employee"]
    inactive = userd.fields_by_name["inactive"]
    dict_ = userd.fields_by_name["dict"]
    others = userd.fields_by_name["others"]
    msg = userd.fields_by_name["msg"]
    map_msg = userd.fields_by_name["map_msg"]

    # assert get_type(code, User)
    assert get_type(age, User) == InnerMessage
    assert get_type(time, User) == Timestamp
    assert get_type(affilliation, User) == str
    assert get_type(name, User) == str
    assert get_type(other, User) == Other
    assert get_type(employee, User) == str
    assert get_type(inactive, User) == bool
    assert get_type(dict_, User) == Dict[str, str]
    assert get_type(others, User) == List[Other]
    assert get_type(msg, User) == ClassMsg
    assert get_type(map_msg, User) == Dict[int, InnerMessage]


def test_cls() -> None:

    ann = inject_proto_typing(User)
    if not User.__annotations__:
        User.__annotations__ = ann
    userann_dict = get_type_hints(User)
    userann = userann_dict.items()

    assert ("age", InnerMessage) in userann
    assert ("time", Timestamp) in userann
    assert ("affilliation", str) in userann
    assert ("name", str) in userann
    assert ("other", Other) in userann
    assert ("employee", str) in userann
    assert ("school", str) in userann
    assert ("inactive", bool) in userann
    assert ("others", List[Other]) in userann
    assert ("dict", Dict[str, str]) in userann
    assert ("msg", ClassMsg) in userann
    assert ("map_msg", Dict[int, InnerMessage]) in userann


def test_inject_typing() -> None:

    User.__annotations__ = {}

    async def get_db() -> str:
        return "sqlite"

    def func(
        other: Annotated[Other, FromRequest(User)],
        code: UserCode = FromRequest(User),
        age: InnerMessage = FromRequest(User),
        time: Timestamp = FromRequest(User),
        name: str = FromRequest(User),
        employee: str = FromRequest(User),
        inactive: bool = FromRequest(User),
        others: List[Other] = FromRequest(User),
        dict: Dict[str, str] = FromRequest(User),
        msg: ClassMsg = FromRequest(User),
        map_msg: Dict[int, InnerMessage] = FromRequest(User),
        code2: UserCode = FromRequest(User, field="code"),
        db: str = Depends(get_db),
    ) -> None:
        pass

    errors = validate_signature_pass(func)
    assert errors == []

    def func2(
        other: Annotated[Other, FromRequest(User)],
    ) -> None:
        pass

    errors = validate_signature_pass(func2)
    assert errors == []
