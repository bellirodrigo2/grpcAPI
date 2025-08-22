import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from example.guber.server.adapters.repo.sqlalchemy.db import Base


class RideDBStatus(enum.Enum):
    REQUESTED = 0
    ACCEPTED = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    CANCELED = 4


class RideDB(Base):
    __tablename__ = "ride"

    ride_id: Mapped[str] = mapped_column(primary_key=True)
    driver_id: Mapped[str] = mapped_column(String, nullable=False)
    passenger_id: Mapped[str] = mapped_column(String, nullable=False)
    start_lat: Mapped[float] = mapped_column(Float, nullable=False)
    start_long: Mapped[float] = mapped_column(Float, nullable=False)
    end_lat: Mapped[float] = mapped_column(Float, nullable=False)
    end_long: Mapped[float] = mapped_column(Float, nullable=False)
    fare: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[RideDBStatus] = mapped_column(Enum(RideDBStatus), nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # One-to-many relationship with positions
    positions: Mapped[List["PositionDB"]] = relationship(
        "PositionDB", back_populates="ride", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<RideDB(ride_id={self.ride_id}, driver_id={self.driver_id}, "
            f"passenger_id={self.passenger_id}, fare={self.fare}, status={self.status}, "
            f"accepted_at={self.accepted_at}, finished_at={self.finished_at})>"
        )


class PositionDB(Base):
    __tablename__ = "position"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ride_id: Mapped[str] = mapped_column(
        String, ForeignKey("ride.ride_id"), nullable=False
    )
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    long: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Many-to-one relationship with ride
    ride: Mapped["RideDB"] = relationship("RideDB", back_populates="positions")

    def __repr__(self):
        return f"<PositionDB(id={self.id}, ride_id={self.ride_id}, lat={self.lat}, long={self.long}, updated_at={self.updated_at})>"
