from sqlalchemy import (
    create_engine,
)

from sqlalchemy.orm import (
    sessionmaker,
)

from textSQL.config.settings import (
    settings,
)


# ============================================================
# ADMIN / MIGRATION ENGINE
# ============================================================

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# TEXT-TO-SQL RUNTIME ENGINE
# ============================================================

runtime_engine = (

    create_engine(
        settings.RUNTIME_DATABASE_URL,
        pool_pre_ping=True,
    )

    if settings.RUNTIME_DATABASE_URL

    else None
)