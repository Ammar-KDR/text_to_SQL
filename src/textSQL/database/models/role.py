from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    role_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )