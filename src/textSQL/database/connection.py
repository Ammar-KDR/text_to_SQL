from sqlalchemy import create_engine

from textSQL.config.settings import settings


engine = create_engine(
    settings.database_url
)