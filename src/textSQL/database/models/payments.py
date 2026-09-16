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


class Payment(Base):
    __tablename__ = "payments"

    payment_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.order_id"),
        nullable=False
    )

    payment_method_id: Mapped[int] = mapped_column(
        ForeignKey("payment_methods.payment_method_id"),
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    payment_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    attempted_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    transaction_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )