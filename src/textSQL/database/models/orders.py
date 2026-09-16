from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=False
    )

    order_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    subtotal_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    shipping_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now(datetime.timezone.utc)
    )