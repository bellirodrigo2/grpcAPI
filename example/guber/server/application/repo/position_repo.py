from datetime import datetime
from typing import Optional

from typing_extensions import Any, Protocol

from example.guber.server.domain import Coord, Position


class PositionRepo(Protocol):

    async def create_position(
        self, ride_id: str, coord: Coord, updated_at: datetime
    ) -> None: ...
    async def get_current_position(self, ride_id: str) -> Optional[Position]: ...
    async def update_position(self, position: Position) -> None: ...


async def get_position_repo(**kwargs: Any) -> PositionRepo:  # type: ignore
    pass
