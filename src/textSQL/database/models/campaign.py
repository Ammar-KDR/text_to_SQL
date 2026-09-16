from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    String,
    DateTime,
    Date,
    Numeric
)
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    campaign_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    campaign_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    campaign_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    budget: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )