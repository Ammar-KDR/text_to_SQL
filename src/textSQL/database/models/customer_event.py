from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class CustomerEvent(Base):
    __tablename__ = "customer_events"

    event_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=False
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )