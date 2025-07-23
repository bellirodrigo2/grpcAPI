from google.protobuf.timestamp_pb2 import Timestamp
from typing_extensions import Dict, List, get_type_hints

from grpcAPI.protobut_typing import get_type, inject_proto_typing
from tests.conftest import ClassMsg, InnerMessage, Other, User


def test_fields() -> None:

    userd = User.DESCRIPTOR

    userd.fields_by_name["code"]
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

    assert get_type(age, User) is InnerMessage
    assert get_type(time, User) is Timestamp
    assert get_type(affilliation, User) is str
    assert get_type(name, User) is str
    assert get_type(other, User) is Other
    assert get_type(employee, User) is str
    assert get_type(inactive, User) is bool
    assert get_type(dict_, User) is Dict[str, str]
    assert get_type(others, User) is List[Other]
    assert get_type(msg, User) is ClassMsg
    assert get_type(map_msg, User) is Dict[int, InnerMessage]


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
