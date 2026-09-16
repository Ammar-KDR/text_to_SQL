from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class CampaignConversion(Base):
    __tablename__ = "campaign_conversions"

    conversion_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.campaign_id"),
        nullable=False
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=False
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.order_id"),
        nullable=False
    )

    attribution_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )