import unittest
from unittest.mock import ANY, call

from grpcAPI.exceptionhandler import ErrorCode
from grpcAPI.testclient.contextmock import ContextMock


class TestContextMock(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = ContextMock()

    def test_peer_tracking(self) -> None:
        self.ctx.peer()
        self.ctx.tracker.peer.assert_called_once_with()

    def test_set_code_and_tracking(self) -> None:
        self.ctx.set_code("OK")
        self.assertEqual(self.ctx.code(), "OK")
        self.ctx.tracker.set_code.assert_called_once_with("OK")

    def test_set_details_and_tracking(self) -> None:
        self.ctx.set_details("Something happened")
        self.assertEqual(self.ctx.details(), "Something happened")
        self.ctx.tracker.set_details.assert_called_once_with("Something happened")

    def test_abort_sets_state_and_raises(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            self.ctx.abort(1, "Error occurred")
        self.assertTrue(self.ctx.was_aborted())
        self.assertEqual(self.ctx.abort_info(), (1, "Error occurred"))
        self.ctx.tracker.abort.assert_called_once_with(1, "Error occurred")

    def test_abort_with_status_sets_state_and_raises(self) -> None:
        class DummyStatus:
            code = 42
            details = "failure"

        with self.assertRaises(RuntimeError) as ctx:
            self.ctx.abort_with_status(DummyStatus())

        self.assertTrue(self.ctx.was_aborted())
        self.assertEqual(self.ctx.abort_info(), (42, "failure"))
        self.ctx.tracker.abort_with_status.assert_called_once_with(ANY)

    def test_add_callback_and_cancel(self) -> None:
        called = []

        def cb():
            called.append(True)

        self.ctx.add_callback(cb)
        self.ctx.cancel()
        self.assertTrue(called)
        self.ctx.tracker.add_callback.assert_called_once()
        self.ctx.tracker.cancel.assert_called_once()

    def test_time_remaining_calls_tracker(self) -> None:
        rem = self.ctx.time_remaining()
        self.assertTrue(rem >= 0.0)
        self.ctx.tracker.time_remaining.assert_called_once_with()

    def test_is_active_default(self) -> None:
        self.assertTrue(self.ctx.is_active())
        self.ctx.tracker.is_active.assert_called_once_with()

    def test_not_implemented_methods(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.ctx.set_compression(1)
        self.ctx.tracker.set_compression.assert_called_once_with(1)

        with self.assertRaises(NotImplementedError):
            self.ctx.disable_next_message_compression()
        self.ctx.tracker.disable_next_message_compression.assert_called_once_with()

        with self.assertRaises(NotImplementedError):
            self.ctx.send_initial_metadata([("key", "value")])
        self.ctx.tracker.send_initial_metadata.assert_called_once_with(
            [("key", "value")]
        )

        with self.assertRaises(NotImplementedError):
            self.ctx.auth_context()
        self.ctx.tracker.auth_context.assert_called_once_with()

    def test_set_trailing_metadata_and_tracking(self) -> None:
        metadata = [("x-trace", "1234")]
        self.ctx.set_trailing_metadata(metadata)
        self.assertEqual(self.ctx.trailing_metadata(), metadata)
        self.ctx.tracker.set_trailing_metadata.assert_called_once_with(metadata)

    def test_invocation_metadata_tracking(self) -> None:
        self.ctx.invocation_metadata()
        self.ctx.tracker.invocation_metadata.assert_called_once_with()

    def test_peer_identity_methods_tracking(self) -> None:
        self.ctx.peer_identities()
        self.ctx.tracker.peer_identities.assert_called_once_with()

        self.ctx.peer_identity_key()
        self.ctx.tracker.peer_identity_key.assert_called_once_with()


class TestContextMockExtended(unittest.TestCase):
    def setUp(self) -> None:
        self.ctx = ContextMock()
        self.ctx.tracker.reset_mock()  # limpar chamadas anteriores se persistentes

    def test_multiple_calls_are_tracked(self) -> None:
        self.ctx.set_code("OK")
        self.ctx.set_code("ERROR")
        self.assertEqual(self.ctx.tracker.set_code.call_count, 2)
        self.ctx.tracker.set_code.assert_has_calls([call("OK"), call("ERROR")])

    def test_call_args_list_example(self) -> None:
        self.ctx.set_details("detail A")
        self.ctx.set_details("detail B")
        expected_calls = [call("detail A"), call("detail B")]
        self.assertEqual(self.ctx.tracker.set_details.call_args_list, expected_calls)

    def test_reset_mock_works(self) -> None:
        self.ctx.set_code("A")
        self.ctx.tracker.set_code.assert_called_once()
        self.ctx.tracker.reset_mock()
        self.ctx.set_code("B")
        self.ctx.tracker.set_code.assert_called_once_with("B")

    def test_time_remaining_is_close(self) -> None:
        remaining = self.ctx.time_remaining()
        self.assertTrue(0 <= remaining <= 60)
        self.ctx.tracker.time_remaining.assert_called_once()

    def test_add_multiple_callbacks_and_cancel(self) -> None:
        flags = []

        def cb1():
            flags.append("cb1")

        def cb2():
            flags.append("cb2")

        self.ctx.add_callback(cb1)
        self.ctx.add_callback(cb2)
        self.ctx.cancel()
        self.assertIn("cb1", flags)
        self.assertIn("cb2", flags)
        self.assertEqual(self.ctx.tracker.add_callback.call_count, 2)
        self.ctx.tracker.cancel.assert_called_once()

    def test_tracker_methods_after_abort(self) -> None:
        with self.assertRaises(RuntimeError):
            self.ctx.abort(10, "aborted!")
        self.assertFalse(self.ctx.is_active())
        self.ctx.tracker.abort.assert_called_once_with(10, "aborted!")
        self.ctx.tracker.is_active.assert_called()

    def test_tracker_methods_after_cancel(self) -> None:
        self.ctx.cancel()
        self.assertFalse(self.ctx.is_active())
        self.ctx.tracker.cancel.assert_called_once()
        self.ctx.tracker.is_active.assert_called()

    def test_abort_then_cancel_then_check_tracker(self) -> None:
        with self.assertRaises(RuntimeError):
            self.ctx.abort(5, "fatal error")
        self.ctx.cancel()
        self.assertFalse(self.ctx.is_active())
        self.ctx.tracker.abort.assert_called_once_with(5, "fatal error")
        self.ctx.tracker.cancel.assert_called_once()


if __name__ == "__main__":
    unittest.main()
