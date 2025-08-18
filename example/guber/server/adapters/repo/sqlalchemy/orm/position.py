from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from example.guber.server.adapters.repo.sqlalchemy.db import Base


class RideDB(Base):
    __tablename__ = "position"

    id: Mapped[str] = mapped_column(primary_key=True)
    ride_id: Mapped[str] = mapped_column(String, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    long: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)