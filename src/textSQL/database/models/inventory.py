from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id: Mapped[int] = mapped_column(
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

    quantity_on_hand: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )

    quantity_reserved: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )