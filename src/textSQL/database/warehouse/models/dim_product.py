from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.warehouse.base import WarehouseBase


class DimProduct(WarehouseBase):
    __tablename__ = "dim_product"
    __table_args__ = {
    "schema": "warehouse"
}

    product_key: Mapped[int] = mapped_column(
        primary_key=True
    )

    product_id: Mapped[int] = mapped_column(
        nullable=False
    )

    variant_id: Mapped[int | None] = mapped_column(
        nullable=True
    )

    product_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    brand_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    sku: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    size: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    color: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )