from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.warehouse.base import WarehouseBase


class DimDate(WarehouseBase):
    __tablename__ = "dim_date"
    __table_args__ = {
    "schema": "warehouse"
}

    date_key: Mapped[int] = mapped_column(
        primary_key=True
    )

    full_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    quarter: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    month: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    month_name: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    week: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    day: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )