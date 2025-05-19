import unittest

from grpcAPI.makeproto.compiler.report import CompileErrorCode, CompileReport


class TestCompileReport(unittest.TestCase):
    def setUp(self) -> None:
        self.report = CompileReport(name="MyTestFile.proto")

    def test_initial_state(self) -> None:
        self.assertTrue(self.report.is_valid())
        self.assertEqual(len(self.report), 0)

    def test_report_single_error(self) -> None:
        self.report.report_error(
            code=CompileErrorCode.INVALID_NAME, location="Line 5: message Foo"
        )
        self.assertFalse(self.report.is_valid())
        self.assertEqual(len(self.report), 1)
        error = self.report.errors[0]
        self.assertEqual(error.code, "E101")
        self.assertEqual(error.location, "Line 5: message Foo")
        self.assertTrue(error.message.startswith("Invalid name"))

    def test_report_multiple_errors(self) -> None:
        self.report.report_error(
            code=CompileErrorCode.MESSAGE_FIELD_MISSING_TYPE,
            location="Line 10: field name",
        )
        self.report.report_error(
            code=CompileErrorCode.DUPLICATE_INDEX, location="Line 12: field id"
        )
        self.assertEqual(len(self.report), 2)
        codes = [e.code for e in self.report.errors]
        self.assertIn("E305", codes)
        self.assertIn("E202", codes)

    def test_override_message(self) -> None:
        custom_msg = "Custom error description"
        self.report.report_error(
            code=CompileErrorCode.INVALID_NAME,
            location="Line 1: message Custom",
            override_msg=custom_msg,
        )
        error = self.report.errors[0]
        self.assertTrue(error.message.endswith(custom_msg))

    def test_show_does_not_crash(self) -> None:
        # Optional display for debugging; not asserting output here
        self.report.report_error(
            code=CompileErrorCode.DUPLICATED_NAME, location="Line 6: field name"
        )
        try:
            self.report.show()
        except Exception as e:
            self.fail(f"report.show() raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
