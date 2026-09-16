from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from textSQL.database.base import Base


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    history_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.order_id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )