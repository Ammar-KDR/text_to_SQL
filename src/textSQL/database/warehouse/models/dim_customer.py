from datetime import date

from sqlalchemy import (
    String,
    Date
)
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.warehouse.base import WarehouseBase


class DimCustomer(WarehouseBase):
    __tablename__ = "dim_customer"
    __table_args__ = {
    "schema": "warehouse"
}

    customer_key: Mapped[int] = mapped_column(
        primary_key=True
    )

    customer_id: Mapped[int] = mapped_column(
        nullable=False
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    customer_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    effective_start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    effective_end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    is_current: Mapped[bool] = mapped_column(
        nullable=False,
        default=True
    )