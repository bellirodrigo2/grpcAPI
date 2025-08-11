from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = "sqlite:///./test.db"  # pode ser PostgreSQL, MySQL etc.

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}  # só necessário no SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
