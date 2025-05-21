import unittest
from enum import Enum
from pathlib import Path
from typing import Dict, List

from grpcAPI.makeproto.compiler import TypeValidator
from grpcAPI.makeproto.compiler.compiler import (
    CompilerContext,
    list_ctx_error_code,
    list_ctx_error_messages,
)
from grpcAPI.types import DEFAULT_PRIMITIVES, String
from grpcAPI.types.message import BaseMessage
from grpcAPI.types.method import Stream
from grpcAPI.types.types import Bytes
from tests.compiler.test_helpers import (
    make_field,
    make_message_block,
    make_method,
    make_service_block,
)


class LabeledEnum(Enum):

    @classmethod
    def protofile(cls) -> str:
        return "foo"

    @classmethod
    def package(cls) -> str:
        return "bar"


class LabeledObject(Enum):

    @classmethod
    def protofile(cls) -> str:
        return "foo"

    @classmethod
    def package(cls) -> str:
        return "bar"


class NonLabeledEnum(Enum):
    pass


class NonCallableEnum(Enum):
    protofile = "hello"
    package = 1


class NotAllowed:
    pass


class Proto2(BaseMessage):
    pass


async def agen():  # type: ignore
    yield "hello"


def not_async():  # type: ignore
    yield "hello"


async def not_gen():  # type: ignore
    return "hello"


class TestTypeValidator(unittest.TestCase):

    def setUp(self) -> None:
        self.block = make_message_block("ValidBlock")
        self.validator = TypeValidator()
        self.context = CompilerContext()
        self.service = make_service_block("Service")

    def test_field_no_type(self) -> None:
        make_field("field1", block=self.block, ftype=None)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E621" for msg in list_ctx_error_code(self.context)))

    def test_field_valid_primitive_type(self) -> None:
        for prim in DEFAULT_PRIMITIVES:
            make_field("field1", block=self.block, ftype=prim)
            self.validator.execute([self.block], self.context)
            self.assertEqual(len(self.context), 0)

    def test_field_labeled_enum_type(self) -> None:
        make_field("field1", block=self.block, ftype=LabeledEnum)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_field_non_labeled_enum_type(self) -> None:
        make_field("field1", block=self.block, ftype=NonLabeledEnum)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertIn(
            'Enum type has no callable "protofile" or "package"',
            list_ctx_error_messages(self.context)[0],
        )
        self.assertTrue(all(msg == "E621" for msg in list_ctx_error_code(self.context)))

    def test_field_non_callable_enum_type(self) -> None:
        make_field("field1", block=self.block, ftype=NonCallableEnum)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertIn(
            'Enum type has no callable "protofile" or "package"',
            list_ctx_error_messages(self.context)[0],
        )
        self.assertTrue(all(msg == "E621" for msg in list_ctx_error_code(self.context)))

    def test_field_invalid_type(self) -> None:
        make_field("field1", block=self.block, ftype=NotAllowed)
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E621" for msg in list_ctx_error_code(self.context)))

    def test_field_list_of_valid_type(self) -> None:
        make_field("field1", block=self.block, ftype=List[int])
        make_field("field1", block=self.block, ftype=List[LabeledEnum])
        make_field("field1", block=self.block, ftype=List[LabeledObject])
        make_field("field1", block=self.block, ftype=List[String])
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_field_list_of_invalid_type(self) -> None:
        make_field("field1", block=self.block, ftype=List[NotAllowed])
        make_field("field1", block=self.block, ftype=List[NonLabeledEnum])
        make_field("field1", block=self.block, ftype=List[Path])
        make_field("field1", block=self.block, ftype=List[List[str]])
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 4)

    def test_field_dict_with_valid_key_and_value(self) -> None:
        make_field("field1", block=self.block, ftype=Dict[str, int])
        make_field("field1", block=self.block, ftype=Dict[str, String])
        make_field("field1", block=self.block, ftype=Dict[str, LabeledEnum])
        make_field("field1", block=self.block, ftype=Dict[str, LabeledObject])
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 0)

    def test_field_dict_with_invalid_key(self) -> None:
        make_field("field1", block=self.block, ftype=Dict[Bytes, int])
        make_field("field1", block=self.block, ftype=Dict[LabeledEnum, String])
        make_field("field1", block=self.block, ftype=Dict[LabeledObject, LabeledEnum])
        make_field("field1", block=self.block, ftype=Dict[List[str], LabeledObject])
        self.validator.execute([self.block], self.context)
        self.assertEqual(len(self.context), 4)

    def test_method_ok_req(self) -> None:
        make_method(
            "Method1",
            request_type=[BaseMessage],
            block=self.service,
            response_type=BaseMessage,
        )
        self.validator.execute([self.service], self.context)
        self.assertEqual(len(self.context), 0)

    def test_method_ok_stream_req(self) -> None:
        make_method(
            "Method1",
            request_type=[Stream[BaseMessage]],
            block=self.service,
            response_type=BaseMessage,
            method_func=agen,
        )
        self.validator.execute([self.service], self.context)
        self.assertEqual(len(self.context), 0)

    def test_method_empty_req(self) -> None:
        make_method(
            "Method1",
            request_type=[],
            block=self.service,
            response_type=BaseMessage,
            method_func=agen,
        )
        self.validator.execute([self.service], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E801" for msg in list_ctx_error_code(self.context)))
        self.assertIn(
            "Method must define a request message",
            list_ctx_error_messages(self.context)[0],
        )

    def test_method_invalid_req(self) -> None:
        make_method(
            "Method1",
            request_type=[str],
            block=self.service,
            response_type=BaseMessage,
            method_func=agen,
        )
        self.validator.execute([self.service], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(all(msg == "E801" for msg in list_ctx_error_code(self.context)))

    def test_method_invalid_req_res(self) -> None:
        make_method(
            "Method1",
            request_type=[str],
            block=self.service,
            response_type=int,
            method_func=agen,
        )
        self.validator.execute([self.service], self.context)
        self.assertEqual(len(self.context), 2)
        self.assertTrue(any(msg == "E801" for msg in list_ctx_error_code(self.context)))
        self.assertTrue(any(msg == "E804" for msg in list_ctx_error_code(self.context)))

    def test_method_many_req(self) -> None:
        make_method(
            "Method1",
            request_type=[BaseMessage, Proto2],
            block=self.service,
            response_type=BaseMessage,
            method_func=agen,
        )
        self.validator.execute([self.service], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(any(msg == "E801" for msg in list_ctx_error_code(self.context)))
        self.assertIn(
            "Only one request message allowed per method",
            list_ctx_error_messages(self.context)[0],
        )

    def test_method_extra(self) -> None:

        validator = TypeValidator(extra_args=[Path, bool])
        make_method(
            "Method1",
            request_type=[BaseMessage, Path, bool],
            block=self.service,
            response_type=Stream[BaseMessage],
            method_func=agen,
        )
        validator.execute([self.service], self.context)
        self.assertEqual(len(self.context), 0)

    def test_method_empty_res(self) -> None:
        make_method(
            "Method1",
            request_type=[Stream[BaseMessage]],
            block=self.service,
            response_type=None,
            method_func=agen,
        )
        self.validator.execute([self.service], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(any(msg == "E804" for msg in list_ctx_error_code(self.context)))
        self.assertIn(
            "Response type is 'None'",
            list_ctx_error_messages(self.context)[0],
        )

    def test_method_invalid_res(self) -> None:
        make_method(
            "Method1",
            request_type=[Stream[BaseMessage]],
            block=self.service,
            response_type=Path,
            method_func=agen,
        )
        self.validator.execute([self.service], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(any(msg == "E804" for msg in list_ctx_error_code(self.context)))
        self.assertIn(
            "Response type is invalid or not a BaseMessage",
            list_ctx_error_messages(self.context)[0],
        )

    def test_method_no_async_res(self) -> None:
        make_method(
            "Method1",
            request_type=[BaseMessage],
            block=self.service,
            response_type=Stream[BaseMessage],
            method_func=not_async,
        )
        self.validator.execute([self.service], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(any(msg == "E805" for msg in list_ctx_error_code(self.context)))

    def test_method_no_gen_res(self) -> None:
        make_method(
            "Method1",
            request_type=[BaseMessage],
            block=self.service,
            response_type=Stream[BaseMessage],
            method_func=not_gen,
        )
        self.validator.execute([self.service], self.context)
        self.assertEqual(len(self.context), 1)
        self.assertTrue(any(msg == "E805" for msg in list_ctx_error_code(self.context)))


if __name__ == "__main__":
    unittest.main()
