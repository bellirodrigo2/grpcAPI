from typing import Tuple

from typing_extensions import Any, Protocol


class PositionRepo(Protocol):

    async def get_current_position(self, ride_id: str) -> Tuple[float, float]: ...


async def get_position_repo(**kwargs: Any) -> PositionRepo:  # type: ignore
    pass
