from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class CustomerCampaign(Base):
    __tablename__ = "customer_campaigns"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.customer_id"),
        primary_key=True
    )

    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.campaign_id"),
        primary_key=True
    )

    interaction_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )