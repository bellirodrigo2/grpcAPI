import pytest

from grpcAPI.testclient.contextmock import ContextMock


@pytest.fixture
def ctx() -> ContextMock:
    return ContextMock()


@pytest.mark.asyncio
async def test_async_methods(ctx: ContextMock) -> None:
    await ctx.write("hello")
    ctx.tracker.write.assert_called_once_with("hello")

    await ctx.send_initial_metadata([("a", "b")])
    ctx.tracker.send_initial_metadata.assert_called_once_with([("a", "b")])

    with pytest.raises(RuntimeError):
        await ctx.abort(1, "error", [("k", "v")])
    ctx.tracker.abort.assert_called_once_with(1, "error", [("k", "v")])


@pytest.mark.asyncio
async def test_read_calls_tracker(ctx: ContextMock) -> None:
    await ctx.read()
    ctx.tracker.read.assert_called_once()


def test_sync_methods(ctx: ContextMock) -> None:
    ctx.set_code("OK")
    ctx.tracker.set_code.assert_called_once_with("OK")
    assert ctx.code() == "OK"

    ctx.set_details("details")
    ctx.tracker.set_details.assert_called_once_with("details")
    assert ctx.details() == "details"

    ctx.set_trailing_metadata([("foo", "bar")])
    ctx.tracker.set_trailing_metadata.assert_called_once_with([("foo", "bar")])
    assert ctx.trailing_metadata() == [("foo", "bar")]

    ctx.invocation_metadata()
    ctx.tracker.invocation_metadata.assert_called_once()

    ctx.peer()
    ctx.tracker.peer.assert_called_once()

    ctx.peer_identities()
    ctx.tracker.peer_identities.assert_called_once()

    ctx.peer_identity_key()
    ctx.tracker.peer_identity_key.assert_called_once()

    ctx.auth_context()
    ctx.tracker.auth_context.assert_called_once()

    ctx.set_compression(2)
    ctx.tracker.set_compression.assert_called_once_with(2)

    ctx.disable_next_message_compression()
    ctx.tracker.disable_next_message_compression.assert_called_once()


def test_timing_and_callbacks(ctx: ContextMock) -> None:
    remaining = ctx.time_remaining()
    assert 0 <= remaining <= 60
    ctx.tracker.time_remaining.assert_called_once()

    assert not ctx.cancelled()
    ctx.tracker.cancelled.assert_called_once()

    assert not ctx.done()
    ctx.tracker.done.assert_called_once()

    def cb():
        return None

    ctx.add_done_callback(cb)
    ctx.tracker.add_done_callback.assert_called_once_with(cb)


def test_tracker_reset(ctx: ContextMock) -> None:
    ctx.set_code("X")
    ctx.tracker.set_code.assert_called_once()
    ctx.tracker.reset_mock()
    ctx.set_code("Y")
    ctx.tracker.set_code.assert_called_once_with("Y")
