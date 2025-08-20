from typing import Tuple

from typing_extensions import Any, Protocol

from example.guber.server.domain import Position


class PositionRepo(Protocol):

    async def get_current_position(self, ride_id: str) -> Tuple[float, float]: ...
    async def update_position(self, position: Position) -> None: ...


async def get_position_repo(**kwargs: Any) -> PositionRepo:  # type: ignore
    pass
