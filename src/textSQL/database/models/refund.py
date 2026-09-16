from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Numeric
)
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class Refund(Base):
    __tablename__ = "refunds"

    refund_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.payment_id"),
        nullable=False
    )

    refund_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    refund_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )