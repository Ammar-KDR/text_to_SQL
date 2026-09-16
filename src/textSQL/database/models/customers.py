from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id"),
        unique=True,
        nullable=True
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )

    customer_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active"
    )

    registered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    last_order_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )