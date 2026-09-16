from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    transaction_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.warehouse_id"),
        nullable=False
    )

    variant_id: Mapped[int] = mapped_column(
        ForeignKey("product_variants.variant_id"),
        nullable=False
    )

    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    quantity_change: Mapped[int] = mapped_column(
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )