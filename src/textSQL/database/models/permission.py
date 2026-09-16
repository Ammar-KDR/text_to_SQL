from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class Permission(Base):
    __tablename__ = "permissions"

    permission_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    permission_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )