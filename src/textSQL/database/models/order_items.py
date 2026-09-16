from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.order_id"),
        nullable=False
    )

    variant_id: Mapped[int] = mapped_column(
        ForeignKey("product_variants.variant_id"),
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    line_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )