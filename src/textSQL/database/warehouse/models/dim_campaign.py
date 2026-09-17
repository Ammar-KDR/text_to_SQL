from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.warehouse.base import WarehouseBase


class DimCampaign(WarehouseBase):
    __tablename__ = "dim_campaign"
    __table_args__ = {
    "schema": "warehouse"
}

    campaign_key: Mapped[int] = mapped_column(
        primary_key=True
    )

    campaign_id: Mapped[int] = mapped_column(
        nullable=False
    )

    campaign_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    campaign_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )