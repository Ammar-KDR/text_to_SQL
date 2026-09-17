from sqlalchemy import (
    String,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.warehouse.base import WarehouseBase


class FactCustomerActivity(WarehouseBase):
    __tablename__ = "fact_customer_activity"
    __table_args__ = {
    "schema": "warehouse"
}
    activity_key: Mapped[int] = mapped_column(
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

    product_key: Mapped[int | None] = mapped_column(
        ForeignKey("warehouse.dim_product.product_key"),
        nullable=True
    )

    campaign_key: Mapped[int | None] = mapped_column(
        ForeignKey("warehouse.dim_campaign.campaign_key"),
        nullable=True
    )

    activity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    activity_count: Mapped[int] = mapped_column(
        nullable=False,
        default=1
    )