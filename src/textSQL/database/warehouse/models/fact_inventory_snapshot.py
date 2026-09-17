from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.warehouse.base import WarehouseBase


class FactInventorySnapshot(WarehouseBase):
    __tablename__ = "fact_inventory_snapshot"
    __table_args__ = {
    "schema": "warehouse"
}

    snapshot_key: Mapped[int] = mapped_column(
        primary_key=True
    )

    date_key: Mapped[int] = mapped_column(
        ForeignKey("warehouse.dim_date.date_key"),
        nullable=False
    )

    product_key: Mapped[int] = mapped_column(
        ForeignKey("warehouse.dim_product.product_key"),
        nullable=False
    )

    warehouse_id: Mapped[int] = mapped_column(
        nullable=False
    )

    quantity_on_hand: Mapped[int] = mapped_column(
        nullable=False
    )

    quantity_reserved: Mapped[int] = mapped_column(
        nullable=False
    )