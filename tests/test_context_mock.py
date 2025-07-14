from unittest.mock import ANY, call

import pytest

from grpcAPI.exceptionhandler import ErrorCode
from grpcAPI.testclient.contextmock import ContextMock


@pytest.fixture
def ctx() -> ContextMock:
    return ContextMock()


def test_peer_tracking(ctx: ContextMock) -> None:
    ctx.peer()
    ctx.tracker.peer.assert_called_once_with()


def test_set_code_and_tracking(ctx: ContextMock) -> None:
    ctx.set_code("OK")
    assert ctx.code() == "OK"
    ctx.tracker.set_code.assert_called_once_with("OK")


def test_set_details_and_tracking(ctx: ContextMock) -> None:
    ctx.set_details("Something happened")
    assert ctx.details() == "Something happened"
    ctx.tracker.set_details.assert_called_once_with("Something happened")


@pytest.mark.asyncio
async def test_abort_sets_state_and_raises(ctx: ContextMock) -> None:
    with pytest.raises(RuntimeError):
        await ctx.abort(1, "Error occurred")
    assert ctx.was_aborted()
    assert ctx.abort_info() == (1, "Error occurred")
    ctx.tracker.abort.assert_called_once_with(1, "Error occurred")


@pytest.mark.asyncio
async def test_abort_with_status_sets_state_and_raises(ctx: ContextMock) -> None:
    class DummyStatus:
        code = 42
        details = "failure"

    with pytest.raises(RuntimeError):
        await ctx.abort_with_status(DummyStatus())

    assert ctx.was_aborted()
    assert ctx.abort_info() == (42, "failure")
    ctx.tracker.abort_with_status.assert_called_once_with(ANY)


@pytest.mark.asyncio
async def test_add_callback_and_cancel(ctx: ContextMock) -> None:
    called = []

    def cb() -> None:
        called.append(True)

    ctx.add_callback(cb)
    await ctx.cancel()
    assert called
    ctx.tracker.add_callback.assert_called_once()
    ctx.tracker.cancel.assert_called_once()


def test_time_remaining_calls_tracker(ctx: ContextMock) -> None:
    rem = ctx.time_remaining()
    assert rem >= 0.0
    ctx.tracker.time_remaining.assert_called_once_with()


def test_is_active_default(ctx: ContextMock) -> None:
    assert ctx.is_active()
    ctx.tracker.is_active.assert_called_once_with()


@pytest.mark.asyncio
async def test_not_implemented_methods(ctx: ContextMock) -> None:
    with pytest.raises(NotImplementedError):
        ctx.set_compression(1)
    ctx.tracker.set_compression.assert_called_once_with(1)

    with pytest.raises(NotImplementedError):
        ctx.disable_next_message_compression()
    ctx.tracker.disable_next_message_compression.assert_called_once_with()

    with pytest.raises(NotImplementedError):
        await ctx.send_initial_metadata([("key", "value")])
    ctx.tracker.send_initial_metadata.assert_called_once_with([("key", "value")])

    with pytest.raises(NotImplementedError):
        ctx.auth_context()
    ctx.tracker.auth_context.assert_called_once_with()


def test_set_trailing_metadata_and_tracking(ctx: ContextMock) -> None:
    metadata = [("x-trace", "1234")]
    ctx.set_trailing_metadata(metadata)
    assert ctx.trailing_metadata() == metadata
    ctx.tracker.set_trailing_metadata.assert_called_once_with(metadata)


def test_invocation_metadata_tracking(ctx: ContextMock) -> None:
    ctx.invocation_metadata()
    ctx.tracker.invocation_metadata.assert_called_once_with()


def test_peer_identity_methods_tracking(ctx: ContextMock) -> None:
    ctx.peer_identities()
    ctx.tracker.peer_identities.assert_called_once_with()

    ctx.peer_identity_key()
    ctx.tracker.peer_identity_key.assert_called_once_with()


# --- Extra tests converted ---


def test_multiple_calls_are_tracked(ctx: ContextMock) -> None:
    ctx.set_code("OK")
    ctx.set_code("ERROR")
    assert ctx.tracker.set_code.call_count == 2
    ctx.tracker.set_code.assert_has_calls([call("OK"), call("ERROR")])


def test_call_args_list_example(ctx: ContextMock) -> None:
    ctx.set_details("detail A")
    ctx.set_details("detail B")
    expected_calls = [call("detail A"), call("detail B")]
    assert ctx.tracker.set_details.call_args_list == expected_calls


def test_reset_mock_works(ctx: ContextMock) -> None:
    ctx.set_code("A")
    ctx.tracker.set_code.assert_called_once()
    ctx.tracker.reset_mock()
    ctx.set_code("B")
    ctx.tracker.set_code.assert_called_once_with("B")


def test_time_remaining_is_close(ctx: ContextMock) -> None:
    remaining = ctx.time_remaining()
    assert 0 <= remaining <= 60
    ctx.tracker.time_remaining.assert_called_once()


@pytest.mark.asyncio
async def test_add_multiple_callbacks_and_cancel(ctx: ContextMock) -> None:
    flags = []

    def cb1():
        flags.append("cb1")

    def cb2() -> None:
        flags.append("cb2")

    ctx.add_callback(cb1)
    ctx.add_callback(cb2)
    await ctx.cancel()
    assert "cb1" in flags
    assert "cb2" in flags
    assert ctx.tracker.add_callback.call_count == 2
    ctx.tracker.cancel.assert_called_once()


@pytest.mark.asyncio
async def test_tracker_methods_after_abort(ctx: ContextMock) -> None:
    with pytest.raises(RuntimeError):
        await ctx.abort(10, "aborted!")
    assert not ctx.is_active()
    ctx.tracker.abort.assert_called_once_with(10, "aborted!")
    ctx.tracker.is_active.assert_called()


@pytest.mark.asyncio
async def test_tracker_methods_after_cancel(ctx: ContextMock) -> None:
    await ctx.cancel()
    assert not ctx.is_active()
    ctx.tracker.cancel.assert_called_once()
    ctx.tracker.is_active.assert_called()


@pytest.mark.asyncio
async def test_abort_then_cancel_then_check_tracker(ctx: ContextMock) -> None:
    with pytest.raises(RuntimeError):
        await ctx.abort(5, "fatal error")
    await ctx.cancel()
    assert not ctx.is_active()
    ctx.tracker.abort.assert_called_once_with(5, "fatal error")
    ctx.tracker.cancel.assert_called_once()
