from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.warehouse.base import WarehouseBase


class FactSales(WarehouseBase):
    __tablename__ = "fact_sales"
    __table_args__ = {
    "schema": "warehouse"
}
    sales_key: Mapped[int] = mapped_column(
        primary_key=True
    )

    date_key: Mapped[int] = mapped_column(
        ForeignKey("warehouse.dim_date.date_key"),
        nullable=False
    )

    customer_key: Mapped[int] = mapped_column(
        ForeignKey("warehouse.dim_customer.customer_key"),
        nullable=False
    )

    product_key: Mapped[int] = mapped_column(
        ForeignKey("warehouse.dim_product.product_key"),
        nullable=False
    )

    category_key: Mapped[int] = mapped_column(
        ForeignKey("warehouse.dim_category.category_key"),
        nullable=False
    )

    campaign_key: Mapped[int | None] = mapped_column(
        ForeignKey("warehouse.dim_campaign.campaign_key"),
        nullable=True
    )

    order_id: Mapped[int] = mapped_column(
        nullable=False
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False
    )

    revenue: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    profit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )