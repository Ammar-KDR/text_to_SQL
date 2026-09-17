from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.warehouse.base import WarehouseBase


class DimCategory(WarehouseBase):
    __tablename__ = "dim_category"
    __table_args__ = {
    "schema": "warehouse"
}

    category_key: Mapped[int] = mapped_column(
        primary_key=True
    )

    category_id: Mapped[int] = mapped_column(
        nullable=False
    )

    category_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    parent_category_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    top_level_category: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    category_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )