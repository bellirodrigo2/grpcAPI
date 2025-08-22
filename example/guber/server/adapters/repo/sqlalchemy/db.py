import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

db_addr = os.getenv("DATABASE_URL")
# DATABASE_URL = f"sqlite+aiosqlite:///{db_addr}"

if db_addr is None:
    raise ValueError("DATABASE_URL environment variable is not set")

DATABASE_URL = db_addr

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db():
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()


class SqlAlchemyDB:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
