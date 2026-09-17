from sqlalchemy import create_engine

from textSQL.config.settings import settings
from sqlalchemy.orm import sessionmaker


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)