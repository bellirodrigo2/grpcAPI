import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from example.guber.server.adapters.repo.sqlalchemy.db import Base


class RideStatus(enum.Enum):
    REQUESTED = 0
    ACCEPTED = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    CANCELED = 4


class RideDB(Base):
    __tablename__ = "ride_requests"

    id: Mapped[str] = mapped_column(primary_key=True)
    passenger_id: Mapped[str] = mapped_column(String, nullable=False)
    from_lat: Mapped[float] = mapped_column(Float, nullable=False)
    fare: Mapped[float] = mapped_column(Float, nullable=False)
    from_long: Mapped[float] = mapped_column(Float, nullable=False)
    to_lat: Mapped[float] = mapped_column(Float, nullable=False)
    to_long: Mapped[float] = mapped_column(Float, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    driver_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[Optional[RideStatus]] = mapped_column(
        Enum(RideStatus), nullable=True
    )
