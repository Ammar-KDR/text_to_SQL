from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    account_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )