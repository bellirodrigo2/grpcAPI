import textwrap
import unittest

from grpcAPI.makeproto.compiler import CompilerContext
from grpcAPI.makeproto.setters.info import (
    OptionsSetter,
    ReservedSetter,
    format_description,
)
from grpcAPI.types import EnumValue
from tests.compilerpasses.test_helpers import (
    make_field,
    make_message_block,
    make_method,
    make_oneof_block,
    make_service_block,
)


class TestInfoSetter(unittest.TestCase):

    def setUp(self) -> None:
        self.block = make_message_block("ValidBlock")
        self.field = make_field("field1", block=self.block)
        self.oneof_block = make_oneof_block(name="oo", block=self.block)
        self.oneof_field = make_field("oo1", block=self.oneof_block)

        self.service = make_service_block("service1")
        self.method = make_method("method1", block=self.service)

        self.optionssetter = OptionsSetter()
        self.reservedsetter = ReservedSetter()
        self.context = CompilerContext()
        self.report = self.context.get_report(self.block.name)

    def test_set_options_ok(self) -> None:
        self.block.options = {
            "foo": "bar",
            "deprecated": True,
            "hello": EnumValue("world"),
        }
        self.optionssetter.execute([self.block, self.service], self.context)
        self.assertEqual(len(self.context), 0)
        self.assertIn(
            'foo = "bar"',
            self.block.render_dict["options"],
        )
        self.assertIn(
            "deprecated = true",
            self.block.render_dict["options"],
        )
        self.assertIn(
            "hello = world",
            self.block.render_dict["options"],
        )

    def test_already_single_line_comment(self) -> None:
        assert (
            format_description("// existing comment", 50, False)
            == "// existing comment"
        )

    def test_already_multiline_comment(self) -> None:
        assert (
            format_description("/* multiline comment */", 50, False)
            == "/* multiline comment */"
        )

    def test_force_format_existing_comment(self) -> None:
        assert (
            format_description("// existing comment", 50, True) == "// existing comment"
        )

    def test_single_line_under_max_chars(self) -> None:
        assert (
            format_description("short description", 50, False) == "// short description"
        )

    def test_single_line_equals_max_chars(self) -> None:
        text = "a" * 50
        assert format_description(text, 50, False) == f"// {text}"

    def test_multiline_comment_when_over_max_chars(self) -> None:
        text = (
            "This is a very long description that should be split into multiple lines"
        )
        expected = "/*\nThis is a very long description that should be\nsplit into multiple lines\n*/"
        assert format_description(text, 50, False) == expected

    def test_multiline_comment_with_newlines(self) -> None:
        text = "This is a line\nand this is another line"
        expected = "/*\nThis is a line and this is another line\n*/"
        assert format_description(text, 50, False) == expected

    def test_always_format_true_for_multiline(self) -> None:
        text = "/* already formatted */"
        expected = "// already formatted"
        assert format_description(text, 50, True) == expected

    def test_removes_prefix_suffix_and_trims(self) -> None:
        text = " /* text with extra spaces */ "
        expected = "// text with extra spaces"
        assert format_description(text, 50, True) == expected

    def test_extremely_long_text(self) -> None:
        text = "word " * 20  # ~100 chars
        expected = "/*\n" + "\n".join(textwrap.wrap(text.strip(), width=30)) + "\n*/"
        assert format_description(text, 30, False) == expected

    def test_reserveds_ok(self) -> None:
        self.block.reserveds = [1, 4, range(5, 9), "foo", "bar", range(12, 45)]
        self.reservedsetter.execute([self.block], self.context)
        reserveds = self.block.render_dict["reserveds"]
        self.assertIn('"foo","bar"', reserveds)
        self.assertIn("1, 4, 5 to 8, 12 to 44", reserveds)
