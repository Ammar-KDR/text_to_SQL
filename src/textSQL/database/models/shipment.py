from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.order_id"),
        nullable=False
    )

    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.warehouse_id"),
        nullable=False
    )

    shipping_method_id: Mapped[int] = mapped_column(
        ForeignKey("shipping_methods.shipping_method_id"),
        nullable=False
    )

    tracking_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    shipment_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    shipped_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )