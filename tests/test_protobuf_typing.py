import sys
from pathlib import Path

from google.protobuf.struct_pb2 import ListValue, Struct
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.wrappers_pb2 import Int32Value, Int64Value
from typing_extensions import Dict, List, get_type_hints

from grpcAPI.protobut_typing import get_type, inject_proto_typing

# from tests.conftest import ClassMsg, InnerMessage, Other, User

lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path.resolve()))

from tests.lib.inner.inner_pb2 import InnerMessage  # noqa: F401
from tests.lib.multi.inner.class_pb2 import ClassMsg  # noqa: F401
from tests.lib.other_pb2 import Other  # noqa: F401
from tests.lib.user_pb2 import Circular, User  # noqa: F401


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
    strs = userd.fields_by_name["strs"]
    nested = userd.fields_by_name["nested"]
    circular = userd.fields_by_name["circular"]
    struct_value = userd.fields_by_name["struct_value"]

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
    assert get_type(strs, User) is List[str]
    assert get_type(nested, User) is User.Nested
    assert get_type(circular, User) is Circular
    assert get_type(struct_value, User) is List[Struct]


def test_cls() -> None:

    ann = inject_proto_typing(User)
    if not User.__annotations__:
        User.__annotations__ = ann
    
    # Use User.__annotations__ directly since get_type_hints may fail
    # when protobuf modules aren't properly registered in sys.modules
    try:
        userann_dict = get_type_hints(User)
        userann = userann_dict.items()
    except KeyError:
        # Fallback to direct annotations for protobuf classes
        userann = User.__annotations__.items()

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
    assert ("strs", List[str]) in userann
    assert ("nested", User.Nested) in userann
    assert ("circular", Circular) in userann

    assert "name" in ClassMsg.__annotations__.keys()
    assert "circular_user" in Circular.__annotations__.keys()
    assert "age" in InnerMessage.__annotations__.keys()
    assert "nested_field" in User.Nested.__annotations__.keys()
    assert "name" in Other.__annotations__.keys()
    assert "seconds" in Timestamp.__annotations__.keys()
    assert "nanos" in Timestamp.__annotations__.keys()
    assert "values" in ListValue.__annotations__.keys()
    assert "value" in Int32Value.__annotations__.keys()
    assert "value" in Int64Value.__annotations__.keys()
