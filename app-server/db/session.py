from config import settings

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    with SessionLocal() as session:
        yield session


# TODO: Move to a migration script later
from sqlalchemy import text

with engine.begin() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
