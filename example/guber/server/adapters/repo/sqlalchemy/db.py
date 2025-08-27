import os
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


AsyncSessionLocal_ = None


def AsyncSessionLocal():
    return AsyncSessionLocal_()


class SqlAlchemyDB:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db


@asynccontextmanager
async def init_db(_: Any):
    db_addr = os.getenv("DATABASE_URL")
    if not db_addr:
        raise ValueError("DATABASE_URL not set")

    engine = create_async_engine(db_addr, echo=False)
    global AsyncSessionLocal_
    AsyncSessionLocal_ = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield
    await engine.dispose()
