from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    Numeric,
    DateTime
)
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class CampaignProduct(Base):
    __tablename__ = "campaign_products"

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.campaign_id"),
        primary_key=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id"),
        primary_key=True
    )

    discount_percentage: Mapped[float | None] = mapped_column(
        Numeric(5, 2),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )