from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from example.guber.db import Base


class Account(Base):
    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    cpf: Mapped[str] = mapped_column(String, nullable=False)
    car_plate: Mapped[Optional[str]] = mapped_column(String)
    is_driver: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )

    __table_args__ = (CheckConstraint("is_driver IN (0, 1)", name="ck_is_driver_bool"),)
