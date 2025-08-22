from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import desc, select
from typing_extensions import Optional

from example.guber.server.adapters.repo.sqlalchemy import (
    AsyncSessionLocal,
    PositionDB,
    SqlAlchemyDB,
)
from example.guber.server.application.repo import PositionRepo
from example.guber.server.domain import Coord, Position


class SqlAlchemyPositionRepo(SqlAlchemyDB, PositionRepo):

    async def create_position(
        self, ride_id: str, coord: Coord, updated_at: datetime
    ) -> None:
        position_db = PositionDB(
            ride_id=ride_id,
            lat=coord.lat,
            long=coord.long,
            updated_at=updated_at,
        )

        self.db.add(position_db)
        await self.db.commit()

    async def get_current_position(self, ride_id: str) -> Optional[Position]:
        result = await self.db.execute(
            select(PositionDB)
            .where(PositionDB.ride_id == ride_id)
            .order_by(desc(PositionDB.updated_at))
            .limit(1)
        )
        position_db = result.scalar_one_or_none()

        if position_db is None:
            return None

        return orm_to_proto(position_db)

    async def update_position(self, position: Position) -> None:
        """Store a new position update"""
        position_db = PositionDB(
            ride_id=position.ride_id,
            lat=position.coord.lat,
            long=position.coord.long,
            updated_at=position.updated_at.ToDatetime(),
        )

        self.db.add(position_db)
        await self.db.commit()


def orm_to_proto(position_db: PositionDB) -> Position:
    """Convert PositionDB to Position proto"""
    position = Position()
    position.ride_id = position_db.ride_id
    position.coord.lat = position_db.lat
    position.coord.long = position_db.long
    position.updated_at.FromDatetime(position_db.updated_at)
    return position


@asynccontextmanager
async def get_position_sqlalchemy_repo() -> AsyncGenerator[PositionRepo, None]:
    db = AsyncSessionLocal()
    try:
        yield SqlAlchemyPositionRepo(db)
    finally:
        await db.close()
